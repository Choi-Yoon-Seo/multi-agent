# Week 2. 에이전트 개발 환경 구축과 실전 준비

> 원본: `docs/ch2.md`

## 학습 목표

- 재현 가능한 에이전트 실습 환경을 직접 만들 수 있다
- MCP, Skills, Instructions, Hooks, Memory가 각각 어떤 역할인지 큰 그림으로 구분할 수 있다
- 실습 결과를 코드, 로그, 출력 파일, 체크리스트로 남기는 습관을 익힐 수 있다
- 3주차 MCP·Skills 실습을 바로 시작할 준비를 마칠 수 있다

---

## 선수 지식

- Python 기초 문법
- VS Code 또는 터미널 사용 경험
- Git의 기본 개념

---

## 2.1 이번 장의 핵심만 먼저

2주차의 핵심은 화려한 기능이 아니라 **실습이 다시 돌아가게 만드는 바닥 작업**이다.

이 장에서 먼저 잡아야 할 것은 네 가지다.

1. **AI가 만든 코드도 환경이 다르면 쉽게 깨진다.**
2. **좋은 실습은 결과를 다시 실행할 수 있어야 한다.**
3. **실습 결과는 코드만이 아니라 로그, 출력 파일, 체크리스트까지 남겨야 한다.**
4. **이번 주에 만든 환경이 3주차 이후 실습의 기반이 된다.**

---

## 2.2 왜 환경이 먼저인가

### 2.2.1 AI가 만든 코드는 왜 자주 깨지는가

- 겉으로는 맞아 보여도 실행 환경 차이를 자주 숨긴다
- 특히 아래 문제가 반복된다
  - 패키지 버전 불일치
  - 운영체제 경로 차이
  - 인코딩 차이
  - 환경 변수와 비밀정보 처리 누락

예를 들어 AI가 예전 `pandas` API를 사용한 코드를 제안하면, 학생 컴퓨터에서는 바로 오류가 날 수 있다.

그래서 에이전트 개발의 첫 역량은 "코드를 잘 생성하는 것"보다 **같은 결과를 다시 실행할 수 있게 만드는 것**이다.

### 2.2.2 "내 컴퓨터에서는 된다"가 왜 위험한가

이 말은 대개 실행 조건이 문서화되지 않았다는 뜻이다.

에이전트 실습에서는 특히 더 위험하다.

- 어떤 도구를 호출했는가
- 어떤 파일을 읽었는가
- 어떤 환경 변수에 의존했는가
- 어떤 결과를 남겼는가

이 정보가 빠지면 실습을 다시 재현하기 어렵다.

### 2.2.3 수업의 기본 규칙

이번 수업에서는 모든 실습을 가능하면 아래 네 가지로 남긴다.

- 코드
- 실행 로그
- 출력 파일
- 체크리스트

이 네 가지가 있어야 나중에 다시 확인하고, 팀원과 공유하고, 다음 주차로 연결하기 쉽다.

---

## 2.3 에이전트 개발의 전체 지도

에이전트 개발은 하나의 기술로 끝나지 않는다.
수업에서는 아래 여섯 층을 구분해서 본다.

| 층위 | 역할 | 대표 예시 |
|------|------|----------|
| 도구 연결 | 외부 시스템과 연결 | MCP |
| 작업 규칙 | 어떤 순서와 기준으로 일할지 정의 | Skills, Instructions |
| 자동 실행 | 특정 이벤트 전후 동작 연결 | Hooks |
| 실행 오케스트레이션 | 단일/복수 에이전트 흐름 제어 | LangChain, LangGraph, Agents SDK |
| 지속 문맥 | 팀 규칙과 장기 컨텍스트 유지 | Memory, Spaces |
| 지식 공급 | 외부 문서와 기억 제공 | RAG |

이번 주차에서는 이 중 전부를 깊게 다루는 것이 아니라, 앞으로의 수업이 어떤 층으로 쌓이는지 감을 잡는 정도면 충분하다.

### 아주 간단히 구분하면

- MCP = 도구 연결
- Skills = 작업 매뉴얼
- Instructions = 기본 규칙
- Hooks = 자동 실행
- Memory = 지속 문맥
- Plugin/App/Connector = 제품별 포장 방식

---

## 2.4 이번 주에 실제로 준비할 것

2주차에서 학생이 실제로 준비해야 하는 것은 아래 정도다.

1. Python 가상환경
2. `requirements.txt`
3. `.env.example`
4. `code/`, `output/`, `logs/`, `docs/` 폴더
5. 최소 실행 스크립트 1개
6. 체크리스트 1개
7. Copilot Agent 사용 가능 여부 확인

즉, 이번 주의 목표는 "대단한 기능 구현"이 아니라 **다음 실습이 안 막히는 시작점**을 만드는 것이다.

---

## 2.5 재현 가능한 로컬 환경 만들기

### 2.5.1 Python 가상환경

프로젝트마다 독립적인 실행 환경을 두기 위해 가상환경을 사용한다.

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

활성화 후에는 `python`과 `pip`가 가상환경 기준으로 동작한다.

### 2.5.2 의존성 기록

같은 결과를 다시 만들려면 버전 기록이 필요하다.

- 기본 파일: `requirements.txt`
- 필요하면: `requirements-dev.txt`

처음에는 아래처럼 단순하게 시작해도 된다.

```bash
pip freeze > requirements.txt
```

핵심은 "무조건 자주 freeze"가 아니라 **성공한 환경을 기록하는 것**이다.

### 2.5.3 `.env`와 `.env.example`

- `.env`: 실제 비밀값 저장
- `.env.example`: 필요한 변수 이름만 공유

예시:

```env
OPENAI_API_KEY=
GITHUB_TOKEN=
PROJECT_NAME=agenticAI
```

`.env`는 반드시 `.gitignore`에 포함한다.

### 2.5.4 폴더 구조 통일

수업 권장 구조:

```text
agenticAI/
  class/
  practice/
  code/
  data/
  output/
  logs/
  docs/
  .env.example
  requirements.txt
  checklist.md
```

실습은 가능하면 저장소 루트의 `code/`, `output/`, `logs/`, `docs/`를 그대로 사용한다.

### 2.5.5 `.gitignore` 최소 규칙

```gitignore
.venv/
__pycache__/
*.pyc
.env
output/
logs/
```

이 규칙은 숨기기용이 아니라 아래를 위한 최소 장치다.

- 민감정보 보호
- 불필요한 파일 제외
- 협업 혼란 방지

---

## 2.6 Copilot 실습 준비

2주차부터의 실습은 **GitHub Copilot 중심**으로 진행한다.

권장 환경:

- VS Code 최신 안정 버전
- GitHub Copilot 확장
- GitHub Copilot Chat 확장

### 최소 확인 절차

1. VS Code에서 Copilot Chat을 연다
2. 채팅 패널에서 **Agent** 모드를 선택할 수 있는지 본다
3. 간단한 프롬프트를 보내 응답이 오는지 확인한다
4. 터미널 명령 제안이 뜰 때 승인 절차가 어떻게 보이는지 확인한다

### 알아두면 좋은 구분

- Agent mode: 복수 파일 수정, 실행, 반복 수정 작업
- MCP: 외부 도구 연결 작업
- Skills: 반복 규칙 주입
- Custom instructions: 저장소 수준 기본 규칙
- Hooks: 작업 전후 자동 검사
- Memory / Spaces: 프로젝트 맥락 유지

---

## 2.7 실습용 프로젝트 템플릿 만들기

### 표준 실행 규칙

모든 실습은 아래 세 질문에 답할 수 있어야 한다.

1. 무엇을 실행했는가
2. 어디에 결과가 저장되었는가
3. 어떻게 검증했는가

### 기본 패턴: 실행 - 검증 - 저장

수업에서 반복해서 사용할 기본 흐름은 다음과 같다.

1. 실행한다
2. 결과를 확인한다
3. 산출물을 파일로 저장한다

이 패턴이 중요한 이유:

- AI가 "성공했다"고 말하는 것과 실제 성공은 다르다
- 파일로 남겨야 나중에 다시 볼 수 있다
- 같은 결과를 다른 사람도 확인할 수 있다

예시 코드:

```python
from pathlib import Path

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

result_path = output_dir / "hello.txt"
result_path.write_text("agent starter is ready\n", encoding="utf-8")

print(f"saved: {result_path}")
```

이 템플릿은 3주차의 MCP 설정, 이후 주차의 LangChain/LangGraph 실습으로 계속 이어진다.

---

## 2.8 체크리스트 습관 만들기

### 작업 전 체크리스트

- 작업 범위
- 입력값
- 제약 조건
- 검증 방법
- 안전 항목

예시:

```markdown
- 작업 범위: starter 프로젝트 구조 생성
- 입력: Python 3.11, 로컬 터미널
- 제약: API 키를 코드에 넣지 않음
- 검증: output/hello.txt 생성 여부 확인
- 안전: .env는 커밋하지 않음
```

### 작업 후 체크리스트

- 실제 실행했는가
- 출력 파일이 생성되었는가
- 로그가 남았는가
- 제약을 어기지 않았는가
- 문제가 있었다면 무엇을 수정했는가

체크리스트는 단순 메모가 아니라:

- 작업 전에는 계획표
- 작업 후에는 검수표

역할을 한다.

---

## 2.9 실습 1: 에이전트 스타터 프로젝트 만들기

### 실습 목표

- Copilot Agent로 실습 프로젝트 구조를 만든다

### 요청 예시

```text
이 저장소에 code, output, logs, docs 폴더를 만들고,
현재 시각을 output/hello.txt에 저장하는 파이썬 스크립트를
code/hello_agent.py로 작성하고 실행해줘.
```

학생은 아래를 확인하면 된다.

- 폴더가 실제로 생성되었는가
- 스크립트가 실행되었는가
- `output/hello.txt`가 남았는가
- 로그나 설명이 남았는가

---

## 2.10 실습 2: 첫 규칙 파일 만들기

### 실습 목표

- Copilot이 자동으로 따르는 기본 규칙 파일을 만든다

### 요청 예시

```text
.github/copilot-instructions.md를 만들어줘. 내용은 이거야:
- 출력 파일은 output/에 저장
- 로그는 logs/에 저장
- 비밀정보는 코드에 직접 쓰지 않음
```

이 파일이 있으면 Copilot이 반복적으로 같은 규칙을 따르기 쉬워진다.

---

## 2.11 제출물

- `code/`, `output/`, `logs/`, `docs/`
- `requirements.txt`
- `.env.example`
- `checklist.md`
- 규칙 파일 1개
- 실행 로그 1개 이상
- 출력 파일 1개 이상

---

## 2.12 핵심 정리

- 에이전트 개발의 출발점은 화려한 자동화가 아니라 **재현 가능한 환경**이다
- 좋은 실습은 코드만이 아니라 **로그, 출력 파일, 체크리스트**까지 함께 남긴다
- MCP, Skills, Instructions, Hooks, Memory는 서로 다른 층위다
- 2주차에서 만든 바닥이 3주차 MCP 실습의 기반이 된다

---

## 2.13 2주차에서 꼭 준비할 것

2주차의 목표는 많은 도구를 배우는 것이 아니라, 이후 실습이 안정적으로 돌아갈 수 있는 기본 환경을 갖추는 것이다.
따라서 이번 장에서는 아래 항목을 확실히 준비하는 것이 중요하다.

### 지금 꼭 있어야 하는 것

- 왜 환경이 먼저인지에 대한 설명
- 가상환경, `requirements.txt`, `.env.example`
- 표준 폴더 구조
- 실행-검증-저장 패턴
- 체크리스트 습관
- Copilot Agent 준비 확인

### 있으면 좋지만 지금은 가볍게 보고 넘어가도 되는 것

- 제품별 세부 차이
- 확장 시스템 비교
- 장기적으로는 필요한 고급 주제들

즉, 2주차는 새로운 기능을 많이 익히는 주차라기보다 **앞으로의 실습을 받쳐 주는 기반을 만드는 주차**에 가깝다.

---

## 부록 A. 다른 도구로 볼 때의 대응 관계

본문을 이해했다면 아래 정도만 잡아도 충분하다.

| 수업 개념 | GitHub Copilot | Codex / ChatGPT | Claude Code 계열 |
|----------|----------------|-----------------|------------------|
| 기본 규칙 | Custom instructions | Rules / `AGENTS.md` | 프로젝트 지침 |
| 작업 규칙 | Skills | Skills | Skills |
| 도구 연결 | MCP | MCP / Apps 뒤쪽 도구 계층 | MCP |
| 지속 문맥 | Memory | Memory | Memory |

핵심은 제품 메뉴를 외우는 것이 아니라, 같은 역할을 다른 이름으로 볼 수 있는가이다.

---

## 참고 자료

- GitHub Copilot agent mode: https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-your-ide
- GitHub Agent Skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- GitHub Copilot CLI: https://docs.github.com/en/free-pro-team%40latest/copilot/how-tos/copilot-cli/use-copilot-cli
- Claude Code IDE integration: https://docs.anthropic.com/en/docs/claude-code/ide-integrations
- Claude Code settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Claude Code hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Codex app: https://openai.com/index/introducing-the-codex-app/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- Apps in ChatGPT: https://help.openai.com/en/articles/11487775-connectors-in-chatgpt

---

## 다음 주 예고

- 3주차에서는 실제로 MCP 서버를 연결하고 호출해 본다
- 같은 작업에 규칙 파일을 적용해 결과의 차이를 비교한다
- 최소 MCP 서버를 직접 구현하며 도구 연결 구조를 체험한다
