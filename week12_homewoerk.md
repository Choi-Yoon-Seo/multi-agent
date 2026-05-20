# 12주차 과제

## GitHub 저장소
- URL: https://github.com/YOONSEO-92/multi-agent

## 내 에이전트
- 에이전트 이름: 취향 기반 플레이리스트 에이전트
- 에이전트 유형:
- 해결하려는 문제: 사용자가 상황과 선호하는 아티스트/장르를 입력하면, 
               그에 맞는 플레이리스트 초안을 생성하는 에이전트
- 입력 자료: 상황 (드라이브·집중·슬플 때 등), 선호 장르, 선호 아티스트
- 결과 파일: draft.md

## 중간 정보 구조
| key                 | 의미                       |
|---------------------|---------------------------|
|  input_id           | 입력 블록 식별자              |
|  situation          | 사용자가 입력한 상황 텍스트      |
|  genre              | 선호 장르 리스트              |
|  artist             | 선호 아티스트 리스트           |
|  음악_속성            | 상황에서 도출된 mood·energy 값 |
|  playlist_structure | 에너지 수준에 따른 구성 계획     |
|  judgment_reason    | 구성 선택 근거 한 줄           |

## 판단/처리 기준
- 기준 1: energy가 "very_high"이면 정점부를 2곡으로 구성
- 기준 2: energy가 "low"이면 정점 없이 도입부 → 마무리로 연결
- 기준 3: 단일 아티스트 비중이 전체의 30%를 초과하면 초과분 제거
- 기준 4: 상황이 매핑 테이블에 없으면 mood: default, energy: medium으로 fallback
- 기준 5: Spotify API 실패 시 빈 리스트 반환 후 기본 흐름 유지

## 실행 명령
- `python3 my_agent.py`

## 실행 결과 요약
- 입력 항목 개수: 1~3개 (사용자 직접 입력)
- 만들어진 중간 정보: input_id/ situation/ genre/ artist/ 음악_속성/ playlist_structure/ 
                 judgment_reason
- 판단/처리 결과: 상황별 mood·energy 매핑 → Spotify 후보곡 수집 → 아티스트 비중 필터링 → 플레이리스트 초안
- 생성된 파일: draft.md

## 오늘 수정한 함수
| 함수 | 역할 | 수정 내용 |
|---|---|---|
| extract_facts | 입력 분석 | analyze_with_rules / analyze_with_groq 분리, USE_LLM 플래그 추가 |
| classify_items | 판단/처리 | playlist_structure·judgment_reason 필드 추가, 상황 매핑 10개로 확장 |
| save_draft | 결과 저장 | draft.md로 플레이리스트 초안 저장 |

## LLM 또는 외부 도구
- LLM 보조 사용: Groq API (USE_LLM = True 시 활성화, 기본값 False)
- 외부 도구/API/파일: Spotify API (후보곡 수집), .env 파일 (API 키 관리)
- fallback 동작: Groq API 실패 시 규칙 기반 분석으로 자동 전환 / Spotify API 실패 시 빈 리스트 반환 후 기본 흐름 유지

## 코딩에이전트에게 준 지시 2개
1. classify_items() 함수가 반환하는 dict에 playlist_structure와 judgment_reason 필드를 추가하고 energy 수준에 따라 구성 계획을 다르게 출력해줘.
2. my_agent.py에 Spotify API 연결 함수를 추가해줘. SPOTIFY_CLIENT_ID와 SPOTIFY_CLIENT_SECRET은 환경변수로만 읽어야 해. fetch_external_context 함수를 따로 만들고 기존 입력 분석 구조는 유지해줘. Spotify API 호출 실패해도 python3 my_agent.py 기본 실행은 가능해야 해.

## 남은 문제
- [ ] Spotify API 없이 실행 시 플레이리스트가 비어있는 문제 → mock 데이터 또는 로컬 곡 목록 fallback 추가 필요
- [ ] 매핑 테이블에 없는 상황 입력 시 기본값으로만 처리되어 상황 특성이 반영되지 않는 문제