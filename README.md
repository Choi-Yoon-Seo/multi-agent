# 취향 기반 플레이리스트 Multi-Agent

간단한 설명
- 상황·장르·아티스트 입력을 받아 상황별 플레이리스트 초안과 상황별 사용자 가이드를 생성하는 실험적 에이전트 모음입니다.

## 기본 실행 방법 (macOS / Windows 공통)
```bash
streamlit run streamlit_app.py
```

## 보조 실행 방법
- macOS (터미널):
```bash
python3 my_agent.py
```
- Windows (명령 프롬프트 / PowerShell):
```powershell
py my_agent.py
```

## 가상환경 활성화 (권장)
- macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- Windows (PowerShell):
```powershell
py -3 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 입력 파일
- 선택적: `sample_input.txt` — Streamlit UI가 있으면 이 파일을 불러올 수 있습니다.
- 또는 UI/CLI에서 다음 형식으로 직접 입력:
```
[입력]
- 상황: 드라이브
- 장르: k-pop
- 아티스트: NCT WISH, RIIZE
```

## 출력 파일
- `output_user_guide.md` — 상황별 사용자 가이드 저장용
- `draft.md` — 플레이리스트 초안(텍스트) 저장용
- `review_report.md` — 가이드 검토 결과(마크다운) 저장용

## 화면에서 확인할 수 있는 결과 (Streamlit UI 기준)
- 추출된 facts (입력에서 파싱된 구조)
- 분류된 항목 (`classified_items`) — 각 상황에 매핑된 음악 속성 등
- 플레이리스트 초안 (텍스트 블록) — 추천 곡 목록 및 간단한 이유
- 상황별 사용자 가이드 (Markdown) — 구성 계획, 추천 목록, 주의할 점 등
- 가이드 검토 리포트(마크다운)
- 외부 데이터 관련 경고(Spotify 실패 등)

## 구현된 에이전트 역할 (4개)
1. 입력 분석 에이전트
   - 규칙 기반(`analyze_with_rules`) 및 Groq LLM(`analyze_with_groq`)으로 입력에서 상황/장르/아티스트를 추출. `extract_facts`가 이를 통합 호출합니다.
2. 상황 분류 에이전트 (`classify_items`)
   - 추출된 facts를 상황 매핑(mood/energy)으로 변환하고, 플레이리스트 구조 판단(`playlist_structure`, `judgment_reason`)을 추가합니다.
3. 추천(외부 컨텍스트) 에이전트 (`recommend_agent`)
   - 3단계 폴백: `spotify_recommend_agent` → `llm_recommend_agent`(Groq) → `rule_recommend_agent`(하드코딩 샘플). 항상 트랙 리스트를 반환하도록 설계되어 있습니다.
4. 플레이리스트 구성 및 이유 생성 에이전트
   - 후보곡 필터링(`filter_tracks_by_situation`), 플레이리스트 흐름 구성(`build_playlist_flow`, 아티스트 점유율 제한 등), 추천 이유 생성(`generate_reason`)을 통해 최종 초안을 만듭니다.

## 현재 한계
- Spotify 기능은 실제 작동을 위해 환경변수(`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`)가 필요합니다. 없으면 폴백 동작이 발생합니다.
- LLM 연동(Groq/OpenAI)은 각 API 키(`GROQ_API_KEY`, `OPENAI_API_KEY`)가 필요합니다. 키가 없거나 호출이 실패하면 규칙 기반 폴백을 사용합니다.
- LLM 기반 기능은 생성적 응답 특성상 환상(hallucination)이 생길 수 있으며, 응답 검증은 제한적입니다.
- `rule_recommend_agent`는 하드코딩된 샘플 트랙을 반환합니다(테스트/데모 목적).
- 에러 처리와 로깅은 최소화되어 있습니다. 운영 수준의 예외 처리나 재시도 로직은 포함되어 있지 않습니다.

## 간단한 워크플로
1. 입력 → 2. `extract_facts` → 3. `classify_items` → 4. `recommend_agent`로 후보곡 수집 → 5. 필터+구성 → 6. `write_playlist_guides`로 가이드 생성 → 7. `review_guides`로 가이드 검토 및 `review_report.md` 저장

---