import streamlit as st
from pathlib import Path

# Import agent functions from my_agent.py. If import fails, show message but keep UI running.
try:
    from my_agent import (
        SAMPLE_INPUT,
        extract_facts,
        classify_items,
        fetch_external_context,
        write_output,
        write_playlist_guides,
        save_user_guides,
        review_guides,
        save_review_report,
        recommend_agent,
    )
    IMPORT_OK = True
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = e

st.set_page_config(page_title="Playlist Agent UI", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.5rem;}
.stButton button{width:100%;background:#1DB954;color:white;border:none;border-radius:10px;font-weight:bold;}
.stButton button:hover{background:#18a449;color:white;}
.playlist-card{padding:15px;border-radius:12px;border:1px solid #333;margin-bottom:10px;background:#181818;color:white;}
.section-card{padding:15px;border-radius:12px;border:1px solid #ddd;background:#fafafa;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;padding:10px'>
    <h1 style='color:#1DB954;margin-bottom:0px;'>
        🎵 AI Playlist Creator
    </h1>
    <p style='color:gray;font-size:18px'>상황에 맞는 플레이리스트를 자동 생성합니다</p>
</div>
""", unsafe_allow_html=True)

if not IMPORT_OK:
    st.error(f"my_agent.py import 실패: {IMPORT_ERROR}")
    st.info("my_agent.py가 제대로 로드되면 Spotify 연동과 전체 기능이 동작합니다. UI는 계속 사용 가능합니다.")

# Sidebar: input area and sample load
st.sidebar.header("입력 (상황 · 장르 · 아티스트)")
st.sidebar.write("한 블록에 하나의 입력을 넣어주세요. 예: \n[나의 플레이리스트 이름]\n- 상황: 드라이브\n- 장르: k-pop\n- 아티스트: NCT WISH, RIIZE")

if "input_text" not in st.session_state:
    # try to load sample_input.txt, else use SAMPLE_INPUT if available
    sample_path = Path("sample_input.txt")
    if sample_path.exists():
        try:
            st.session_state.input_text = sample_path.read_text(encoding="utf-8")
        except Exception:
            st.session_state.input_text = SAMPLE_INPUT if IMPORT_OK else ""
    else:
        st.session_state.input_text = SAMPLE_INPUT if IMPORT_OK else ""

input_text = st.sidebar.text_area("입력 텍스트", value=st.session_state.input_text, height=240, key="input_area")

if st.sidebar.button("샘플 불러오기"):
    sample_path = Path("sample_input.txt")
    if sample_path.exists():
        try:
            st.session_state.input_area = sample_path.read_text(encoding="utf-8")
            st.sidebar.success("sample_input.txt를 불러왔습니다.")
        except Exception as e:
            st.sidebar.error(f"샘플 파일 읽기 실패: {e}")
    else:
        # fallback to SAMPLE_INPUT constant if available
        if IMPORT_OK:
            st.session_state.input_area = SAMPLE_INPUT
            st.sidebar.info("로컬 sample_input.txt가 없어 SAMPLE_INPUT을 불러왔습니다.")
        else:
            st.sidebar.warning("sample_input.txt가 없고 SAMPLE_INPUT을 사용할 수 없습니다.")

run = st.sidebar.button("🎵 플레이리스트 생성", use_container_width=True)

# Area to show warnings from fetch failures
fetch_warnings = []

# Placeholders for results
facts = None
classified = None
playlist_draft = None
guides_md = None

if run:
    if not IMPORT_OK:
        st.error("my_agent 모듈이 로드되지 않아 실행할 수 없습니다.")
    else:
        # 1. extract_facts
        try:
            facts = extract_facts(input_text)
        except Exception as e:
            st.error(f"입력 분석 실패: {e}")
            facts = []

        # 2. classify_items
        try:
            classified = classify_items(facts)
        except Exception as e:
            st.error(f"상황 분류 실패: {e}")
            classified = []

        # 3. recommend_agent per item (try/except)
        if classified:
            for item in classified:
                try:
                    rec = recommend_agent(item)
                    if isinstance(rec, dict):
                        item["tracks"] = rec.get("tracks", [])
                        status = rec.get("status")
                        if status != "spotify" and status != "groq":
                            fetch_warnings.append(f"{item.get('input_id')}: 외부 데이터 없음 (fallback to rule)")
                    else:
                        item["tracks"] = []
                        fetch_warnings.append(f"{item.get('input_id')}: 외부 컨텍스트 불명")
                except Exception as e:
                    item["tracks"] = []
                    fetch_warnings.append(f"{item.get('input_id')}: recommend 실패 - {e}")

        # 4. write_output
        try:
            playlist_draft = write_output(classified)
        except Exception as e:
            st.error(f"플레이리스트 작성 실패: {e}")
            playlist_draft = ""

        # 5. write_playlist_guides
        try:
            guides_md = write_playlist_guides(classified)
        except Exception as e:
            st.error(f"가이드 작성 실패: {e}")
            guides_md = ""

# Layout: two columns then full-width guide
col1, col2 = st.columns([1, 1])

with col1:
    exp1 = st.expander("🤖 Agent 분석 결과", expanded=True)
    with exp1:
        if facts is None and classified is None:
            st.info("왼쪽 사이드바에서 입력을 넣고 '실행'을 눌러 결과를 확인하세요.")
        else:
            st.subheader("추출된 facts")
            st.json(facts)
            st.subheader("분류된 항목 (classified_items)")
            st.json(classified)

with col2:
    exp2 = st.expander("🎧 플레이리스트 초안", expanded=False)
    with exp2:
        if playlist_draft is None:
            st.info("실행 후 플레이리스트 초안이 표시됩니다.")
        else:
            if fetch_warnings:
                st.warning("⚠️ 외부 데이터 관련 경고가 있습니다. 아래를 확인하세요.")
                for w in fetch_warnings:
                    st.warning(w)
            st.markdown("---")
            st.markdown("### 🎵 플레이리스트 초안")
            # show as preformatted text for readability
            st.code(playlist_draft, language=None)

# Full-width expander for guides
exp3 = st.expander("📖 상황별 사용자 가이드", expanded=False)
with exp3:
    if guides_md is None:
        st.info("실행 후 상황별 가이드가 표시됩니다.")
    else:
        st.markdown("---")
        st.markdown(guides_md)
        # Save button
        if st.button("가이드 저장 (output_user_guide.md)"):
            try:
                saved = save_user_guides(guides_md)
                st.success(f"가이드 저장 완료: {saved}")
            except Exception as e:
                st.error(f"가이드 저장 실패: {e}")
        # Review the guides and show results (review_guides now returns Markdown string)
        try:
            review_report = review_guides(guides_md)
            st.markdown("---")
            st.subheader("🔍 가이드 검토 결과")
            # Render the markdown report
            st.markdown(review_report)
            if st.button("검토 보고서 저장 (review_report.md)"):
                try:
                    saved_r = save_review_report(review_report)
                    st.success(f"검토 리포트 저장 완료: {saved_r}")
                except Exception as e:
                    st.error(f"검토 리포트 저장 실패: {e}")
        except Exception as e:
            st.error(f"가이드 검토 실패: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("실행 방법: `streamlit run streamlit_app.py`")
st.sidebar.caption("참고: Spotify API 키가 없으면 외부 데이터 수집이 실패할 수 있습니다. 이 경우에도 UI는 계속 동작합니다.")
