import streamlit as st
from pathlib import Path

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
        export_playlist_to_youtube,
    )
    IMPORT_OK = True
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = e

st.set_page_config(page_title="AI Playlist Creator", layout="wide", page_icon="▶️")

st.markdown("""
<style>
/* ── 전체 배경 ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f0f0f !important;
    color: #f1f1f1 !important;
}
[data-testid="stSidebar"] {
    background-color: #212121 !important;
    border-right: 1px solid #303030;
}
[data-testid="stSidebar"] * {
    color: #f1f1f1 !important;
}

/* ── 메인 패딩 ── */
.block-container { padding-top: 1.8rem; padding-bottom: 2rem; }

/* ── 헤더 배너 ── */
.yt-header {
    background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
    border-bottom: 2px solid #ff0000;
    padding: 18px 24px 14px 24px;
    margin-bottom: 24px;
    border-radius: 0 0 8px 8px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.yt-logo { color: #ff0000; font-size: 2.2rem; }
.yt-title { color: #f1f1f1; font-size: 1.7rem; font-weight: 700; margin: 0; }
.yt-sub   { color: #aaaaaa; font-size: 0.9rem; margin: 2px 0 0 0; }

/* ── 섹션 타이틀 ── */
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f1f1;
    letter-spacing: 0.03em;
    margin: 6px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #303030;
    margin-left: 8px;
}

/* ── 카드 ── */
.yt-card {
    background: #1a1a1a;
    border: 1px solid #303030;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.yt-card:hover {
    border-color: #555;
    transition: border-color 0.2s;
}

/* ── 트랙 아이템 ── */
.track-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: #1a1a1a;
    border-left: 3px solid #ff0000;
    transition: background 0.15s;
}
.track-item:hover { background: #222; }
.track-num {
    color: #ff0000;
    font-weight: 700;
    font-size: 1rem;
    min-width: 24px;
    margin-top: 1px;
}
.track-name  { color: #f1f1f1; font-weight: 600; font-size: 0.97rem; }
.track-artist{ color: #aaaaaa; font-size: 0.85rem; }
.track-reason{ color: #888; font-size: 0.8rem; margin-top: 2px; font-style: italic; }

/* ── 배지 ── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 5px;
}
.badge-red   { background: #ff0000; color: white; }
.badge-gray  { background: #303030; color: #aaa; }
.badge-green { background: #2d7a2d; color: #90ee90; }

/* ── 버튼 ── */
.stButton > button {
    background: #ff0000 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 8px 18px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background: #cc0000 !important;
    color: white !important;
}

/* ── 사이드바 버튼 강조 ── */
[data-testid="stSidebar"] .stButton > button {
    background: #ff0000 !important;
    width: 100% !important;
    padding: 10px !important;
    font-size: 1rem !important;
    border-radius: 6px !important;
}

/* ── Expander 스타일 ── */
[data-testid="stExpander"] {
    background: #1a1a1a !important;
    border: 1px solid #303030 !important;
    border-radius: 10px !important;
    margin-bottom: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #f1f1f1 !important;
    font-weight: 600 !important;
}

/* ── input / textarea ── */
.stTextArea textarea, .stTextInput input {
    background: #212121 !important;
    color: #f1f1f1 !important;
    border: 1px solid #404040 !important;
    border-radius: 6px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #ff0000 !important;
    box-shadow: 0 0 0 2px rgba(255,0,0,0.2) !important;
}

/* ── 구분선 ── */
hr { border-color: #303030 !important; }

/* ── 성공/경고/에러 ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── YouTube URL 박스 ── */
.yt-url-box {
    background: #1a1a1a;
    border: 1px solid #ff0000;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 12px;
    text-align: center;
}
.yt-url-box a {
    color: #ff4444;
    font-weight: 700;
    font-size: 1.05rem;
    text-decoration: none;
}
.yt-url-box a:hover { color: #ff0000; text-decoration: underline; }

/* ── 진행 상태 ── */
.step-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    color: #aaa;
    font-size: 0.88rem;
}
.step-done { color: #90ee90 !important; }
.step-dot  { width: 8px; height: 8px; border-radius: 50%; background: #303030; }
.step-dot-done { background: #ff0000 !important; }

/* label 색상 */
label, .stTextArea label, .stTextInput label { color: #aaaaaa !important; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ──────────────────────────────────────────
st.markdown("""
<div class="yt-header">
  <span class="yt-logo">▶</span>
  <div>
    <div class="yt-title">AI Playlist Creator</div>
    <div class="yt-sub">상황 · 장르 · 아티스트를 입력하면 맞춤 플레이리스트를 자동 생성합니다</div>
  </div>
</div>
""", unsafe_allow_html=True)

if not IMPORT_OK:
    st.error(f"⚠️ my_agent.py 로드 실패: {IMPORT_ERROR}")
    st.info("my_agent.py가 같은 디렉터리에 있는지 확인하세요. UI는 계속 사용 가능합니다.")

# ── 사이드바 ──────────────────────────────────────
st.sidebar.markdown("""
<div style='padding:8px 0 14px 0;'>
  <span style='font-size:1.3rem;'>▶</span>
  <span style='font-size:1.1rem;font-weight:700;color:#f1f1f1;margin-left:8px;'>Playlist Creator</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div style='color:#aaa;font-size:0.82rem;margin-bottom:6px;'>입력 형식 예시</div>", unsafe_allow_html=True)
st.sidebar.code("[나의 플레이리스트]\n- 상황: 드라이브\n- 장르: k-pop\n- 아티스트: NCT WISH, RIIZE", language=None)

if "input_text" not in st.session_state:
    sample_path = Path("sample_input.txt")
    if sample_path.exists():
        try:
            st.session_state.input_text = sample_path.read_text(encoding="utf-8")
        except Exception:
            st.session_state.input_text = SAMPLE_INPUT if IMPORT_OK else ""
    else:
        st.session_state.input_text = SAMPLE_INPUT if IMPORT_OK else ""

input_text = st.sidebar.text_area("📝 입력 텍스트", value=st.session_state.input_text, height=220, key="input_area")

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("샘플 불러오기", key="sample_btn"):
        sample_path = Path("sample_input.txt")
        if sample_path.exists():
            try:
                st.session_state.input_area = sample_path.read_text(encoding="utf-8")
                st.sidebar.success("불러오기 완료")
            except Exception as e:
                st.sidebar.error(f"실패: {e}")
        else:
            if IMPORT_OK:
                st.session_state.input_area = SAMPLE_INPUT
                st.sidebar.info("SAMPLE_INPUT 사용")
            else:
                st.sidebar.warning("샘플 없음")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
run = st.sidebar.button("▶  플레이리스트 생성", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='color:#555;font-size:0.78rem;'>실행: <code>streamlit run streamlit_app.py</code></div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='color:#555;font-size:0.78rem;margin-top:4px;'>Spotify API 없으면 fallback 동작</div>", unsafe_allow_html=True)

# ── 상태 변수 ─────────────────────────────────────
fetch_warnings = []
facts = None
classified = None
playlist_draft = None
guides_md = None

# ── 실행 로직 ─────────────────────────────────────
if run:
    if not IMPORT_OK:
        st.error("my_agent 모듈이 로드되지 않아 실행할 수 없습니다.")
    else:
        progress_placeholder = st.empty()

        def show_steps(steps):
            html = "<div class='yt-card' style='margin-bottom:16px;'>"
            html += "<div class='section-title'>⚙️ 처리 중</div>"
            for label, done in steps:
                dot_cls = "step-dot-done" if done else "step-dot"
                row_cls = "step-done" if done else ""
                icon = "✓" if done else "·"
                html += f"<div class='step-row {row_cls}'><div class='step-dot {dot_cls}'></div>{icon} {label}</div>"
            html += "</div>"
            progress_placeholder.markdown(html, unsafe_allow_html=True)

        steps = [
            ("입력 분석", False), ("상황 분류", False),
            ("후보곡 수집", False), ("플레이리스트 작성", False), ("가이드 생성", False)
        ]
        show_steps(steps)

        try:
            facts = extract_facts(input_text)
            steps[0] = (steps[0][0], True); show_steps(steps)
        except Exception as e:
            st.error(f"입력 분석 실패: {e}"); facts = []

        try:
            classified = classify_items(facts)
            st.session_state["classified"] = classified
            steps[1] = (steps[1][0], True); show_steps(steps)
        except Exception as e:
            st.error(f"상황 분류 실패: {e}"); classified = []

        if classified:
            for item in classified:
                try:
                    rec = recommend_agent(item)
                    if isinstance(rec, dict):
                        item["tracks"] = rec.get("tracks", [])
                        if rec.get("status") not in ("spotify", "groq"):
                            fetch_warnings.append(f"{item.get('input_id')}: fallback (rule)")
                    else:
                        item["tracks"] = []
                        fetch_warnings.append(f"{item.get('input_id')}: 외부 컨텍스트 불명")
                except Exception as e:
                    item["tracks"] = []
                    fetch_warnings.append(f"{item.get('input_id')}: recommend 실패 - {e}")
        steps[2] = (steps[2][0], True); show_steps(steps)

        try:
            playlist_draft = write_output(classified)
            steps[3] = (steps[3][0], True); show_steps(steps)
        except Exception as e:
            st.error(f"플레이리스트 작성 실패: {e}"); playlist_draft = ""

        try:
            guides_md = write_playlist_guides(classified)
            steps[4] = (steps[4][0], True); show_steps(steps)
        except Exception as e:
            st.error(f"가이드 작성 실패: {e}"); guides_md = ""

        progress_placeholder.empty()

# ── 메인 레이아웃 ──────────────────────────────────
col1, col2 = st.columns([1, 1])

# ── 왼쪽: Agent 분석 결과
with col1:
    st.markdown("<div class='section-title'>🤖 Agent 분석 결과</div>", unsafe_allow_html=True)
    with st.expander("추출된 Facts / 분류 항목 보기", expanded=bool(facts)):
        if facts is None:
            st.markdown("<div style='color:#555;padding:10px;'>생성 버튼을 눌러 결과를 확인하세요.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#aaa;font-size:0.82rem;margin-bottom:4px;'>추출된 facts</div>", unsafe_allow_html=True)
            st.json(facts)
            st.markdown("<div style='color:#aaa;font-size:0.82rem;margin:10px 0 4px 0;'>분류된 항목</div>", unsafe_allow_html=True)
            st.json(classified)

# ── 오른쪽: 플레이리스트 카드 뷰
with col2:
    st.markdown("<div class='section-title'>🎵 추천 플레이리스트</div>", unsafe_allow_html=True)
    if playlist_draft is None:
        st.markdown("<div class='yt-card' style='color:#555;text-align:center;padding:30px;'>플레이리스트가 아직 없습니다.<br>왼쪽 사이드바에서 생성해보세요.</div>", unsafe_allow_html=True)
    else:
        if fetch_warnings:
            with st.expander("⚠️ 경고 메시지", expanded=False):
                for w in fetch_warnings:
                    st.warning(w)

        # 트랙 파싱해서 카드 형태로 렌더링
        lines = playlist_draft.strip().split("\n")
        current_section = ""
        track_html = ""
        import re
        for line in lines:
            line = line.strip()
            if line.startswith("==="):
                continue
            elif re.match(r"^\[입력\]|^상황:", line) or ("플레이리스트" in line and not re.match(r"^\d+\.", line)):
                if track_html:
                    st.markdown(track_html + "</div>", unsafe_allow_html=True)
                    track_html = ""
                st.markdown(f"<div class='section-title' style='margin-top:14px;'>📋 {line}</div>", unsafe_allow_html=True)
                track_html = "<div>"
            elif re.match(r"^\d+\.", line):
                m = re.match(r"^(\d+)\.\s+(.+?)\s+-\s+(.+)$", line)
                if m:
                    num, artist, title = m.group(1), m.group(2), m.group(3)
                    track_html += f"""
<div class='track-item'>
  <div class='track-num'>{num}</div>
  <div>
    <div class='track-name'>{title}</div>
    <div class='track-artist'>{artist}</div>
"""
            elif line.startswith("이유:"):
                reason = line.replace("이유:", "").strip()
                track_html += f"<div class='track-reason'>💬 {reason}</div></div></div>"
        if track_html:
            st.markdown(track_html + "</div>", unsafe_allow_html=True)

# ── 가이드 섹션
st.markdown("<div class='section-title' style='margin-top:20px;'>📖 상황별 사용자 가이드</div>", unsafe_allow_html=True)
with st.expander("가이드 펼치기", expanded=False):
    if guides_md is None:
        st.markdown("<div style='color:#555;padding:10px;'>플레이리스트 생성 후 가이드가 표시됩니다.</div>", unsafe_allow_html=True)
    else:
        st.markdown(guides_md)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("💾 가이드 저장", key="save_guide"):
                try:
                    saved = save_user_guides(guides_md)
                    st.success(f"저장 완료: {saved}")
                except Exception as e:
                    st.error(f"저장 실패: {e}")
        try:
            review_report = review_guides(guides_md)
            st.markdown("---")
            st.markdown("<div class='section-title'>🔍 가이드 검토 결과</div>", unsafe_allow_html=True)
            st.markdown(review_report)
            with col_g2:
                if st.button("💾 검토 보고서 저장", key="save_review"):
                    try:
                        saved_r = save_review_report(review_report)
                        st.success(f"저장 완료: {saved_r}")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
        except Exception as e:
            st.error(f"가이드 검토 실패: {e}")

# ── YouTube 내보내기 섹션
st.markdown("<div class='section-title' style='margin-top:20px;'>▶️ YouTube 재생목록 내보내기</div>", unsafe_allow_html=True)
with st.expander("YouTube로 내보내기", expanded=False):
    classified_data = st.session_state.get("classified")
    if classified_data is None:
        st.markdown("<div style='color:#555;padding:10px;'>플레이리스트를 먼저 생성하세요.</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class='yt-card'>
  <div style='color:#aaa;font-size:0.88rem;margin-bottom:12px;'>
    생성된 플레이리스트의 모든 곡을 YouTube에서 검색해 재생목록으로 만듭니다.<br>
    <span style='color:#555;font-size:0.8rem;'>※ client_secret.json이 같은 폴더에 있어야 합니다.</span>
  </div>
</div>
""", unsafe_allow_html=True)
        yt_title = st.text_input("🎬 재생목록 이름 (비워두면 자동 생성)", value="", key="yt_title")

        if st.button("▶  YouTube 재생목록 생성", key="yt_export"):
            if not IMPORT_OK:
                st.error("my_agent 모듈이 로드되지 않아 실행할 수 없습니다.")
            else:
                with st.spinner("YouTube에 업로드 중입니다..."):
                    try:
                        title = yt_title.strip() if yt_title.strip() else None
                        yt_url = export_playlist_to_youtube(classified_data, playlist_title=title)
                        if yt_url:
                            st.success("🎉 YouTube 재생목록이 생성되었습니다!")
                            st.markdown(f"""
<div class='yt-url-box'>
  <div style='color:#aaa;font-size:0.82rem;margin-bottom:6px;'>재생목록 URL</div>
  <a href='{yt_url}' target='_blank'>▶ 재생목록 바로가기</a>
  <div style='color:#555;font-size:0.78rem;margin-top:6px;'>{yt_url}</div>
</div>
""", unsafe_allow_html=True)
                        else:
                            st.error("재생목록 생성 실패. YouTube 인증(client_secret.json)을 확인하세요.")
                    except Exception as e:
                        st.error(f"YouTube 내보내기 실패: {e}")