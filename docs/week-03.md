# Week 3. MCP와 Skills 실전 입문

> 원본: docs/ch3.md

## 학습 목표

- MCP가 무엇을 해결하는지 실제 사례로 설명할 수 있다
- 외부 MCP 서버(Playwright MCP)를 설치하고 브라우저 자동화를 실제로 수행할 수 있다
- 외부 skill을 탐색·설치하고 작업 품질 향상 효과를 비교할 수 있다
- GitHub Copilot에서 skill 또는 instruction 파일을 작성하고 적용 효과를 비교할 수 있다
- 최소 MCP 서버를 직접 구현하고 테스트할 수 있다

---

## 선수 지식

- 2주차에서 구축한 `agenticAI/` 저장소의 실습 환경
- Python 기초 문법
- 가상환경과 `.env` 사용법

---

## 3.1 왜 이제는 MCP만 알아서는 부족한가

### 3.1.1 도구만 연결해도 일이 잘 안 되는 이유

- 에이전트에게 도구를 연결했다고 해서 자동으로 좋은 결과가 나오지는 않음
- 이유:
  - 어떤 도구를 언제 써야 하는지 판단이 불명확할 수 있음
  - 출력 형식이 들쭉날쭉할 수 있음
  - 검증 절차 없이 결과를 바로 수락할 수 있음
- 즉, 도구 연결만으로는 "할 수 있는 일"이 늘어날 뿐이고, "잘 일하는 방식"까지 보장하지는 않음

### 3.1.2 규칙 없는 에이전트의 한계

- 규칙이 없으면 에이전트는 같은 요청에도 매번 다른 방식으로 행동할 수 있음
- 흔한 문제:
  - 출력 위치가 바뀜
  - 파일 이름이 일관되지 않음
  - 검증 없이 바로 종료함
  - 위험한 동작을 무심코 시도함
- 그래서 **도구 연결(MCP)**과 함께 **작업 규칙(Skills / Instructions)**이 필요함

### 3.1.3 제품마다 확장 방식이 다른 현실

- 2026년의 도구 생태계는 아직 완전히 하나로 통일되어 있지 않음
- 같은 기능이라도 제품마다 붙이는 방식이 다를 수 있음
  - 어떤 제품은 MCP 서버를 직접 붙임
  - 어떤 제품은 skill 파일이나 instruction 파일을 함께 사용함
  - 어떤 제품은 settings로 기본 동작을 고정함
- 따라서 실무 역량은 "한 제품의 메뉴를 외우는 것"이 아니라, 각 층위의 역할을 구분하는 데서 시작함

---

## 3.2 MCP와 Skills의 역할 구분

### 3.2.1 MCP

- MCP(Model Context Protocol)는 에이전트가 외부 도구와 데이터를 사용할 수 있게 하는 표준 인터페이스
- 질문으로 바꾸면:
  - "에이전트가 무엇을 호출할 수 있는가?"
- 대표 사례:
  - 파일 읽기
  - GitHub 이슈 조회
  - 브라우저 자동화
  - 외부 API 호출

### 3.2.2 Skills / Instructions

- Skills 또는 Instructions는 에이전트가 작업할 때 따라야 할 규칙과 절차를 담음
- 질문으로 바꾸면:
  - "에이전트가 어떤 순서와 기준으로 일해야 하는가?"
- 대표 사례:
  - 출력은 반드시 `output/`에 저장
  - 위험한 명령은 사용자 승인 없이 실행하지 않음
  - 테스트를 먼저 실행하고 실패 시 원인을 기록

### 3.2.3 둘을 혼동하면 생기는 문제

- MCP를 배웠다고 해서 Skills까지 배운 것은 아님
- skill 파일을 만들었다고 해서 외부 도구 연결이 생기는 것도 아님
- 좋은 에이전트 환경은 **도구 연결(MCP)**과 **작업 규칙(Skills)**을 함께 갖출 때 완성됨

**표 3.1** 주요 개념의 차이

| 개념 | 핵심 질문 | 역할 |
|------|----------|------|
| MCP | 무엇을 호출할 수 있는가 | 도구 연결 |
| Skills / Instructions | 어떻게 일하게 할 것인가 | 작업 규칙 |

---

## 3.3 MCP 빠른 이해

### 3.3.1 MCP가 해결하는 문제

- AI 도구마다 외부 시스템 연결 방식이 제각각이면 재사용이 어려움
- 같은 기능을 플랫폼마다 다시 구현해야 함
- MCP는 이 문제를 줄이기 위해 도구 연결 방식을 표준화하려는 접근임

### 3.3.2 Tools, Resources, Prompts

- MCP는 보통 세 가지 요소를 중심으로 설명됨
  - **Tools**: AI가 호출하는 함수
  - **Resources**: AI가 읽는 컨텍스트 데이터
  - **Prompts**: 재사용 가능한 프롬프트 자산

- 이 수업에서는 먼저 **Tools** 중심으로 실습함
- 이유:
  - 가장 체감이 빠름
  - 도구 호출 로그를 확인하기 쉬움
  - 이후 LangChain, LangGraph와 연결하기 좋음

### 3.3.3 STDIO와 Remote MCP

- 로컬 실습에서는 보통 STDIO 기반 MCP를 먼저 접함
  - 클라이언트가 서버 프로세스를 실행
  - 표준 입력/출력으로 메시지를 주고받음
- 원격 MCP는 네트워크를 통해 서버에 연결함
  - 인증과 권한 관리가 더 중요해짐

### 3.3.4 승인, 권한, 보안 경계

- MCP를 쓰는 이유 중 하나는 무제한 접근이 아니라 **제한된 접근**을 만들기 위해서임
- 예를 들어:
  - 파일 읽기는 허용
  - 파일 삭제는 금지
  - 특정 폴더 밖 접근은 금지
- 따라서 좋은 MCP 서버는 "많이 할 수 있는 서버"보다 "무엇을 못 하게 할지 분명한 서버"에 가까움

### 3.3.5 MCP 서버의 토큰 소비 문제와 대응

- MCP 서버를 연결하면 실제 호출 여부와 무관하게 **모든 툴 스키마가 세션 시작 시 컨텍스트에 로드**됨
- 시스템 프롬프트, 툴, MCP 서버, 에이전트, 대화 내용 전부가 하나의 컨텍스트 윈도우(보통 200k 토큰) 안에서 경쟁함

#### 실제 소비 규모

- 한 사례에서는 MCP 툴 스키마만으로 **81,986 토큰(전체의 41%)**이 소비됨
- 서버별 예시:
  - playwright-mcp: 22개 툴 → 약 14,300 토큰 (200k의 7.2%)
  - Jira MCP 단독으로 약 17,000 토큰
  - 5개 서버 조합 시 55,000 토큰 이상이 대화 시작 전에 소모됨
- 빈 대화 상태에서 자유 공간이 5%밖에 남지 않는 경우도 발생함

#### 대응 1: Tool Search (자동)

- MCP 툴 설명이 컨텍스트 윈도우의 10%를 초과하면 일부 에이전트가 자동으로 **Tool Search**를 활성화함
- 이 경우 MCP 툴이 즉시 로드되지 않고 **지연(defer)**되며, 실제 필요한 툴만 온디맨드로 검색해서 로드함
- 전통적 방식 대비 토큰 사용량을 약 85% 줄이며, 도구 선택 정확도도 개선됨

#### 대응 2: 세션별 서버 관리 (수동)

- 세션마다 **필요한 MCP 서버만 활성화**하는 것이 핵심
- `/context` 명령으로 현재 토큰 소비 현황을 확인할 수 있음
- `/mcp`로 서버별 토큰 비용을 확인하고 불필요한 서버를 비활성화할 수 있음

> **⚠️ 좀비 프로세스 주의**
>
> MCP 서버를 설정에서 제거하거나 비활성화해도 **이미 실행 중인 프로세스는 자동으로 종료되지 않는다.**
> 특히 stdio 기반 MCP 서버(npx로 실행)는 백그라운드에서 계속 살아 있을 수 있으며, 연결이 끊긴 상태에서 **CPU를 100% 점유하며 폭주**하는 경우도 발생한다.
>
> ```bash
> # 1. 잔존 MCP 프로세스 확인
> ps aux | grep -i "mcp" | grep -v grep
>
> # 2. 정상 종료 시도
> kill <PID>
>
> # 3. 응답하지 않으면 강제 종료
> kill -9 <PID>
> ```
>
> MCP 서버를 제거하거나 교체한 후에는 반드시 프로세스 확인 습관을 들이는 것이 좋다.

#### 대응 3: Skill로 대체

- MCP 서버 대신 **Skill을 활용**하면 초기 로드 시 약 200 토큰만 소비하고, 실제 호출 시에만 전체 내용이 로드됨
- 예: Playwright를 5회 중 1회만 사용한다면, 나머지 4 세션에서 약 10,000 토큰을 절약할 수 있음
- 따라서 자주 쓰지 않는 도구는 MCP 상시 연결보다 Skill 호출 방식이 효율적임

#### 이 문제가 실습에서 중요한 이유

- "MCP 서버를 많이 붙이면 더 강력해진다"는 직관은 틀림
- 실제로는 **도구가 늘어날수록 컨텍스트가 좁아지고 대화 품질이 떨어짐**
- 좋은 설계는 "필요한 도구만 필요한 시점에 로드하는 것"임
- 이 감각은 이후 멀티에이전트, LangGraph 실습에서도 반복적으로 중요해짐

---

## 3.4 실습 1: Playwright MCP 설치하고 브라우저 자동화하기

### 실습 목표

- 외부 MCP 서버(Playwright MCP)를 설치하고, 에이전트가 실제 브라우저를 제어하는 과정을 체험한다

### Playwright MCP란

- Microsoft가 만든 공식 MCP 서버로, Playwright 브라우저 자동화를 에이전트에게 연결한다
- 브라우저의 **접근성 트리(accessibility tree)**를 읽어 구조화된 페이지 정보를 반환함
- 비전 모델 없이도 웹 페이지를 이해하고 조작할 수 있음
- 25개 이상의 브라우저 자동화 도구를 제공함

### 주요 도구 목록

| 도구 | 설명 |
|------|------|
| `browser_navigate` | URL로 이동 |
| `browser_snapshot` | 접근성 트리(페이지 구조) 반환 |
| `browser_take_screenshot` | 스크린샷 캡처 |
| `browser_click` | 요소 클릭 |
| `browser_type` | 텍스트 입력 |
| `browser_fill_form` | 폼 여러 필드 동시 입력 |
| `browser_select_option` | 드롭다운 선택 |
| `browser_press_key` | 키보드 입력 전송 |
| `browser_evaluate` | JavaScript 실행 |
| `browser_wait_for` | 텍스트 출현 대기 |
| `browser_console_messages` | 콘솔 로그 조회 |
| `browser_network_requests` | 네트워크 요청 목록 |

### 설치 방법 A: GitHub Copilot (VS Code)

`.vscode/mcp.json`에 추가한다:

```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

또는 VS Code Command Palette에서 `MCP: Add Server`를 선택한다.

### 설치 방법 B: 프로젝트 공유용 (.mcp.json)

프로젝트 루트에 `.mcp.json`을 만들어 팀 전체가 공유할 수 있다:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--headless` | 브라우저 창 없이 실행 (CI/서버 환경) |
| `--browser firefox` | 브라우저 종류 선택 (chrome, firefox, webkit) |
| `--caps vision` | 좌표 기반 클릭 등 비전 모드 활성화 |
| `--caps pdf` | 페이지를 PDF로 저장 |
| `--caps testing` | 요소 존재 검증, 텍스트 확인 등 테스트 도구 |
| `--viewport-size 1920x1080` | 뷰포트 크기 설정 |
| `--device "iPhone 15"` | 모바일 기기 에뮬레이션 |

### 수행 단계

1. 위 방법 중 하나로 Playwright MCP를 설치한다
2. 에이전트에게 다음과 같이 요청한다

```text
https://news.ycombinator.com 을 열고 상위 5개 헤드라인을 요약해줘.
```

3. 에이전트가 `browser_navigate` → `browser_snapshot`을 호출하는 과정을 관찰한다
4. 다음 요청도 시도한다

```text
https://example.com 에 접속해서 스크린샷을 찍고,
페이지 구조를 설명해줘.
```

5. 폼 입력이 필요한 사이트에서도 시도한다

```text
https://www.google.com 에 접속해서 검색창에 "Playwright MCP"를 입력하고
검색 결과 상위 3개를 알려줘.
```

### 관찰 포인트

- 에이전트가 어떤 도구를 어떤 순서로 호출하는가
- 접근성 트리 기반 정보와 스크린샷 정보의 차이는 무엇인가
- 승인 요청은 언제 나타나는가
- 실패하는 경우는 어떤 사이트이고 왜 실패하는가

### 결과 기록 예시

```markdown
- 호출 도구: browser_navigate → browser_snapshot
- 입력: url=https://news.ycombinator.com
- 결과: 상위 30개 게시물 제목, 점수, 댓글 수 반환
- 검증: 실제 사이트와 비교 완료
- 관찰: 접근성 트리만으로 충분한 정보를 얻을 수 있었음. 로그인 필요 사이트에서는 실패함
```

### 2026년 참고: MCP vs CLI

- 파일 시스템 접근이 가능한 에이전트(GitHub Copilot Coding Agent 등)에서는 **Playwright CLI**(`@playwright/cli`)가 MCP보다 토큰 효율이 약 4배 높음
- MCP는 세션당 약 114,000 토큰, CLI는 약 27,000 토큰을 사용함
- CLI는 스냅샷과 스크린샷을 디스크에 YAML 파일로 저장하고 에이전트가 필요한 부분만 읽음
- 파일 시스템 접근이 없는 클라이언트(Cursor 등)에서는 MCP가 여전히 권장됨

---

## 3.5 실습 2: 외부 Skills 탐색하고 설치하기

### 실습 목표

- 커뮤니티와 공식 마켓플레이스에서 유용한 skill을 찾아 설치하고, 실제 작업에 적용한다

### Skill이란

- Skill은 에이전트가 특정 작업을 수행할 때 따르는 **규칙과 절차를 담은 파일**이다
- MCP가 "무엇을 할 수 있는가"라면, Skill은 "어떻게 잘 할 것인가"에 해당한다
- GitHub Copilot에서는 `.github/skills/` 디렉토리에 `SKILL.md` 파일로 정의한다
- Copilot coding agent, Copilot CLI, VS Code Insiders에서 지원된다

### GitHub Copilot Agent Skills 구조

```text
.github/skills/<skill-name>/
  SKILL.md          # 필수 — 스킬 정의 파일
  examples/          # 선택 — 예시 파일
  templates/         # 선택 — 템플릿 파일
```

- `SKILL.md`에는 YAML 프론트매터와 본문을 함께 적음
- **중요 제약**: `name` 필드는 소문자+하이픈만 허용하며, **부모 디렉토리 이름과 반드시 일치**해야 함
- `description`은 Copilot이 언제 이 skill을 자동 선택할지 결정하는 핵심 필드

```markdown
---
name: doc-summary
description: Summarize documents and save to output/. Use for file summarization, documentation review.
---

# Document Summary Skill

Read the target document, summarize it, save the result in output/, and list 3 verification checks.
```

### 학생에게 유용한 외부 Skill 예시

#### 추천 1: 코드 요약·문서화 Skill

과제 코드를 자동으로 요약하고 문서를 생성한다.

```markdown
---
name: code-documenter
description: Generate documentation for source code. Use when asked to document, explain, or summarize code files.
---

# Code Documentation Skill

1. Read the target source file
2. Summarize the purpose of each function/class
3. List input/output for public APIs
4. Save the result to output/<filename>-docs.md
5. Include 3 verification checks at the end
```

- 이 skill을 `.github/skills/code-documenter/SKILL.md`에 저장하면 Copilot이 자동으로 인식한다
- 학생은 이 예시를 기반으로 자신의 과제에 맞는 skill을 직접 작성해 본다

#### 추천 2: 테스트 생성 Skill

작성한 코드에 대해 테스트 코드를 자동으로 생성한다.

```markdown
---
name: test-generator
description: Generate test cases for source code. Use when asked to write tests, create test files, or verify code.
---

# Test Generator Skill

1. Read the target source file
2. Identify all public functions and edge cases
3. Generate test cases using the project's testing framework
4. Include at least: 1 happy path, 1 edge case, 1 error case per function
5. Save to tests/<filename>_test.py (or appropriate extension)
6. Run the tests and report results
```

#### 추천 3: 과제 제출 검증 Skill

제출 전 과제가 요구사항을 충족하는지 체크한다.

```markdown
---
name: assignment-checker
description: Verify assignment deliverables are complete. Use when asked to check, validate, or review homework.
---

# Assignment Checker Skill

1. Read the assignment requirements from the specified file
2. List all required deliverables
3. Check each deliverable exists and is non-empty
4. Verify output/ directory contains expected files
5. Generate a checklist with ✅/❌ status for each item
6. Save the checklist to output/assignment-check.md
```

### 오픈소스 Skill 참고 자료

- Agent Skills 표준은 여러 에이전트 도구가 동일한 `SKILL.md` 형식을 공유함
- 아래 저장소에서 다른 사람이 만든 skill을 참고하고 자신의 것으로 변형할 수 있다

| 사이트 | URL | 설명 |
|--------|-----|------|
| Agent Skills 표준 | agentskills.io | 오픈 표준 명세 |
| GitHub Agent Skills 문서 | docs.github.com/en/copilot/concepts/agents/about-agent-skills | 공식 가이드 |
| Anthropic Skills | github.com/anthropics/skills | 공식 skill (구조 참고) |
| awesome-claude-skills | github.com/travisvn/awesome-claude-skills | 커뮤니티 skill 디렉토리 |

### 수행 단계

1. 위 추천 skill 중 1개를 `.github/skills/`에 만든다
2. skill 없이 같은 작업을 한 번 수행한다
3. skill을 적용한 후 같은 작업을 다시 수행한다
4. 두 결과를 비교한다

### 비교 실습 예시

**skill 없이:**

```text
이 Python 코드를 리뷰해줘.
```

**code-review skill 설치 후:**

```text
이 Python 코드를 리뷰해줘.
보안, 테스트 가능성, 유지보수성 기준으로 분석해줘.
```

### 관찰 포인트

- skill이 적용되었을 때 출력 구조가 얼마나 더 체계적인가
- 같은 요청에 대해 검토 항목이 더 구체적으로 나오는가
- 어떤 종류의 skill이 학업에 실질적으로 도움이 되는가

---

## 3.6 실습 3: Skill / Instruction 파일 직접 작성

### 실습 목표

- 같은 작업을 "규칙 없이" 했을 때와 "규칙 있게" 했을 때의 차이를 비교한다

### 과제 설명

- 작업 하나를 고른다
  - 예: 파일 요약
  - 예: 테스트 코드 생성
  - 예: 로그 정리
- 먼저 규칙 없이 요청한다
- 다음으로 아래와 같은 규칙 파일을 만든 뒤 같은 요청을 다시 한다

- GitHub Copilot 기준 최신 실습 방식
  - Agent mode에서는 instruction 파일로 먼저 비교 실습을 한다
  - Agent Skills는 공식 문서 기준 Copilot coding agent, Copilot CLI, VS Code Insiders에서 우선 지원되므로, Skills 실습은 **VS Code Insiders 또는 Copilot CLI** 기준으로 수행한다

예시 규칙:

```markdown
# 작업 규칙

- 출력 파일은 반드시 output/ 디렉토리에 저장한다.
- 결과를 바로 확정하지 말고 핵심 검증 항목 3개를 먼저 적는다.
- 불확실한 정보는 추측하지 말고 확인 필요라고 표시한다.
- 실행 후 logs/에 실행 내용을 남긴다.
```

### 비교 항목

- 출력 형식이 더 일관적인가
- 누락이 줄어들었는가
- 검증 항목이 더 명확해졌는가
- 안전성이 높아졌는가

### Agent Skills 실습 예시

- VS Code Insiders 또는 Copilot CLI를 사용할 수 있다면 다음 구조를 권장함

```text
.github/skills/doc-summary/
  SKILL.md
  examples/
  templates/
```

- `SKILL.md`에는 YAML 프론트매터와 본문을 함께 적음

```markdown
---
name: doc-summary
description: Summarize documents and save to output/. Use for file summarization, documentation review.
---

# Document Summary Skill

Read the target document, summarize it, save the result in output/, and list 3 verification checks.
```

- **중요 제약**: `name` 필드는 소문자+하이픈만 허용하며, **부모 디렉토리 이름과 반드시 일치**해야 함 (예: 디렉토리가 `doc-summary/`이면 `name: doc-summary`)
- `description`은 Copilot이 언제 이 skill을 자동 선택할지 결정하는 핵심 필드이므로 구체적으로 작성함

### 실습 확장: custom instructions 추가

- 같은 규칙을 저장소 수준 instruction으로 옮겨 본다
- 학생은 비교한다
  - skill로 넣었을 때
  - instruction으로 넣었을 때
  - 둘의 역할이 어떻게 다른가

#### `.instructions.md` 경로별 지시 (2025년 중반 추가)

- `.github/copilot-instructions.md`는 저장소 전체에 적용되는 지시 파일 (프론트매터 불필요)
- `.github/instructions/*.instructions.md`는 **특정 경로에만 적용**되는 지시 파일

```markdown
---
applyTo: "src/components/**/*.ts,src/components/**/*.tsx"
---

컴포넌트 파일은 반드시 테스트 파일과 함께 작성한다.
출력은 항상 output/에 저장한다.
```

- `applyTo`에 글롭 패턴을 쉼표로 구분해 넣으면 해당 파일 편집 시에만 지시가 활성화됨
- 학생은 skill과 path-scoped instruction의 역할 차이를 비교해야 함

### 실습의 의도

- 이 실습은 "규칙을 적으면 에이전트가 항상 완벽해진다"를 보여주려는 것이 아님
- 오히려 다음 사실을 체감하게 하려는 것임
  - 규칙이 없으면 결과가 흔들린다
  - 규칙을 적으면 검토가 쉬워진다

---

## 3.7 테스트와 검증

### 3.7.1 AI 없이 단독 테스트하는 법

- MCP 서버는 가능하면 AI 없이도 테스트할 수 있어야 함
- 이유:
  - 문제 원인을 분리하기 쉬움
  - 모델 출력과 서버 오류를 구분할 수 있음

### 3.7.2 정상 입력 / 오류 입력 테스트

- 최소한 두 종류의 테스트가 필요함
  - 정상 입력
  - 잘못된 입력

- 예:
  - 정상 경로 입력 시 파일 목록 반환
  - 존재하지 않는 경로 입력 시 읽기 쉬운 오류 반환

### 3.7.3 로그와 산출물 남기기

- 다음 파일을 남기는 습관을 들임
  - 실행 로그
  - 출력 예시
  - 설계 문서
  - 비교 메모
- 이 기록은 나중에 LangChain, LangGraph 실습으로 넘어갈 때 매우 중요함

---

## 3.8 제출물

- Playwright MCP 연결 설정 파일 및 실행 로그
- skill 또는 instruction 파일 1개
- skill 적용 전후 비교 결과 문서
- 테스트 로그
- 업데이트된 체크리스트

---

## 3.9 핵심 정리

- MCP는 도구 연결이다
- Skills / Instructions는 작업 규칙이다
- 외부 MCP 서버(Playwright 등)를 설치하면 에이전트의 능력이 크게 확장된다
- 외부 skill을 탐색·설치하면 작업 품질과 일관성이 높아진다
- 좋은 설계는 필요한 도구만 필요한 시점에 로드하는 것이다
- 실제 활용 역량은 MCP와 Skills를 함께 다룰 때 생긴다
- 3주차의 산출물은 이후 LangChain, LangGraph, 멀티에이전트 실습의 입력 자산이 된다

---

## 부록 A. ChatGPT / Codex로 수행하는 동일 실습

- OpenAI 쪽은 이름이 조금 다르지만, 같은 층위로 매핑할 수 있다
  - MCP = 외부 도구 연결
  - Skills = Codex app/CLI/IDE에서의 skill 또는 rules 계층

### A.1 ChatGPT에서의 외부 도구 연결

- 2025년 12월부터 OpenAI는 connectors를 **Apps**로 통합해 안내함
- ChatGPT 쪽에서 외부 기능을 붙이는 현재 개념은 **Apps**임
- 학생은 여기서 "ChatGPT 안에 외부 기능을 붙인다"는 감각을 익히면 된다

### A.2 ChatGPT Apps 실습

- ChatGPT에서 앱 디렉터리를 열고 앱 하나를 연결한다
- 권장 실습:
  1. 앱 디렉터리에서 GitHub나 문서 검색 계열 앱을 찾는다
  2. 연결 가능한 앱을 활성화한다
  3. 다음과 같이 요청한다

```text
연결된 앱을 사용해서 이 저장소 또는 연결된 문서에서 week3 실습과 관련된 정보를 찾아 요약해줘.
```

- 관찰 포인트
  - 앱이 어떤 정보를 검색·참조하는가
  - 단순 채팅과 무엇이 다른가
  - ChatGPT Apps가 MCP와 같은 표준인지, 아니면 제품 표면인지 구분할 수 있는가

### A.3 ChatGPT의 MCP 실습

- ChatGPT는 2025년 9월부터 **Developer Mode**를 통해 MCP를 지원함
  - 설정 경로: Settings → Connectors → Advanced → Developer Mode
- **중요 제약**: ChatGPT MCP는 **원격 HTTPS 서버만 연결 가능**. localhost 서버에는 연결할 수 없음
- ChatGPT App Directory에 등록된 서드파티 앱은 내부적으로 MCP 서버로 구현됨
- 핵심 메시지:
  - ChatGPT Apps는 사용자 표면
  - MCP는 그 뒤쪽의 도구 연결 표준

### A.4 Codex에서의 Skills / Rules 실습

- Codex는 ChatGPT 계정으로 사용하는 코딩 에이전트이며, 다음 표면을 함께 제공한다
  - Terminal / CLI (Rust 기반 오픈소스)
  - IDE 확장 (VS Code 등)
  - Codex App (웹/클라우드)
  - GitHub (`@codex` 태그로 이슈·PR에서 호출)
  - Slack (`@Codex` 태그로 채널에서 호출)
  - ChatGPT iOS 앱
- 공식 안내 기준 Codex는 skills, rules, `AGENTS.md` 기능을 제공한다
- **`AGENTS.md`**: 저장소 수준의 지침 파일로, Codex가 프로젝트를 이해하는 방법을 정의함
  - 우선순위: `AGENTS.override.md` > `AGENTS.md` > `TEAM_GUIDE.md` > `.agents.md`
- 3주차 실습에서는 다음과 같이 수행한다

```text
이 저장소를 읽고 docs/notes.md를 요약해줘.
반드시 output/summary.md에 저장하고, 검증 항목 3개를 함께 적어줘.
```

- 그리고 규칙을 준 뒤 다시 비교한다

```text
다음 규칙을 지켜줘:
- 출력은 output/에 저장
- 검증 항목 3개 작성
- 불확실한 내용은 추측하지 말 것
이 규칙을 지키면서 docs/notes.md를 다시 요약해줘.
```

### A.5 Codex의 MCP 실습

- Codex는 CLI와 IDE 확장 모두에서 MCP를 지원함
- Codex CLI 자체가 **MCP 서버로도 동작**할 수 있어, OpenAI Agents SDK 등 외부 에이전트가 Codex를 도구로 호출하는 구조도 가능함
- 수업에서는 다음 수준까지 실습하는 것을 목표로 한다
  - Codex가 MCP 서버를 쓰는 환경이라는 점을 이해한다
  - 같은 작업을 "도구 없이"와 "MCP 연결 후" 비교한다

### A.6 OpenAI 부록의 의도

- OpenAI 표면은 이름이 바뀌기 쉬우므로 학생이 가장 먼저 익혀야 할 것은 메뉴 이름이 아니라 구조임
- 이 부록의 핵심 대응 관계:
  - GitHub Copilot MCP ↔ ChatGPT Apps / Developer Mode MCP
  - GitHub Skills ↔ Codex skills / rules
  - GitHub custom instructions ↔ Codex AGENTS.md
- 목적은 특정 제품 조작법 암기가 아니라, **동일한 실습 구조를 다른 벤더 표면으로 번역하는 능력**을 기르는 것임

---

## 부록 B. Gemini CLI로 수행하는 동일 실습

- Google의 터미널 기반 AI 코딩 에이전트로, GitHub Copilot CLI와 비슷한 구조를 가진다
- MCP, Skills, Extensions 계층이 모두 존재한다
- 2026년 3월 기준 최신 버전: **v0.34.0**

### B.1 설치

```bash
# npm으로 설치
npm install -g @anthropic-ai/gemini-cli   # 실제 패키지명은 공식 문서 확인
# 또는 공식 설치 스크립트
curl -fsSL https://geminicli.com/install.sh | bash
```

- 설치 후 `gemini` 명령으로 실행한다
- Google 계정 인증이 필요하며, Gemini API 키 또는 Google Cloud 프로젝트를 연결한다

### B.2 Instructions — GEMINI.md

- GitHub Copilot의 `copilot-instructions.md`에 대응하는 파일이 `GEMINI.md`이다
- 계층 구조:

| 위치 | 범위 |
|------|------|
| `~/.gemini/GEMINI.md` | 전역 — 모든 프로젝트에 적용 |
| 프로젝트 루트 `GEMINI.md` | 프로젝트 — 해당 워크스페이스에만 적용 |
| 하위 디렉토리 `GEMINI.md` | 컴포넌트 — 해당 디렉토리 접근 시 자동 로드 |

- 모든 발견된 파일은 합쳐져서 매 프롬프트에 포함됨
- `@file.md` 구문으로 다른 파일을 import할 수 있음

### B.3 Skills 실습

- GitHub Copilot과 **같은 오픈 표준**을 사용한다 — `SKILL.md` 형식이 동일함
- 스킬 위치:

| 위치 | 범위 |
|------|------|
| `.gemini/skills/` 또는 `.agents/skills/` | 워크스페이스 — 버전 관리에 포함 |
| `~/.gemini/skills/` 또는 `~/.agents/skills/` | 사용자 — 전역 개인용 |
| Extension 내부 | 확장 — 설치된 Extension에 번들된 스킬 |

- 동작 흐름:
  1. 세션 시작 시 스킬 이름+설명만 시스템 프롬프트에 주입 (전체 내용 아님)
  2. 작업이 스킬과 매칭되면 `activate_skill` 호출
  3. 사용자 동의 후 전체 `SKILL.md`와 폴더 구조가 컨텍스트에 로드
- 관리 명령: `/skills` (인터랙티브) 또는 `gemini skills` (터미널)

### B.4 MCP 서버 연결

- `.gemini/settings.json` 또는 `~/.gemini/settings.json`에서 설정한다
- 세 가지 트랜스포트 지원: **stdio**, **SSE**, **HTTP Streaming**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN"
      }
    }
  }
}
```

- 주요 옵션:
  - `trust`: `true`면 도구 호출 확인을 건너뜀
  - `includeTools` / `excludeTools`: 특정 도구만 허용하거나 차단
  - `timeout`: 요청 타임아웃 (기본 600,000ms)

### B.5 Extensions (확장 시스템)

- Gemini CLI만의 강점이다
- 스킬 + MCP 서버 + 커맨드를 **하나의 패키지로 묶어** 설치·공유할 수 있다
- 설치/관리:

```bash
# GitHub에서 설치
gemini extensions install <github-url>

# 로컬 경로에서 설치
gemini extensions install ./my-extension

# 새 확장 프로젝트 생성
gemini extensions new path/to/directory mcp-server
```

- [공식 카탈로그](https://geminicli.com/extensions/)에서 Google, Figma, Shopify, Stripe 등 파트너 확장을 탐색할 수 있음

### B.6 Gemini CLI 부록의 의도

- GitHub Copilot과 가까운 구조를 가지고 있어 직접 비교 학습이 가능하다
- 핵심 대응 관계:
  - `copilot-instructions.md` ↔ `GEMINI.md`
  - `.github/skills/` ↔ `.gemini/skills/` (동일 표준)
  - Copilot MCP 설정 ↔ Gemini MCP 설정 (거의 동일)
  - 없음 ↔ Extensions 카탈로그 (Gemini만의 강점)
- 목적은 "같은 개념이 다른 도구에서 어떻게 표현되는지"를 체감하는 것이다

---

## 부록 C. Google Antigravity로 수행하는 동일 실습

- Google의 에이전틱 IDE로, VS Code 포크 기반이다
- 2025년 11월 발표, 2026년 3월 기준 **퍼블릭 프리뷰(무료)**, 최신 버전: v1.20.3
- Editor View(코드 편집), Manager View(다중 에이전트 관리), Browser Integration(웹 조작) 세 가지 표면을 가진다
- 멀티 모델 지원: Gemini 3 Pro/Flash, Claude Sonnet 4.5/Opus 4.6, GPT-OSS-120B

### C.1 설치

- [antigravity.google](https://antigravity.google)에서 플랫폼별 설치 파일을 다운로드한다
- macOS, Windows, Linux 모두 지원
- VS Code 또는 Cursor에서 설정, 확장, 키바인딩을 가져올 수 있다
- 확장은 **OpenVSX 레지스트리**를 사용하므로, VS Code Marketplace 전용 확장(Pylance, Remote-SSH 등)은 수동 `.vsix` 설치가 필요하다

### C.2 Instructions — Rules 시스템

- 3단계 우선순위를 가진 규칙 파일:

| 우선순위 | 파일 | 설명 |
|---------|------|------|
| 1 (최고) | `GEMINI.md` | Antigravity 전용 규칙 |
| 2 | `AGENTS.md` | 크로스 도구 공유 규칙 (v1.20.3에서 추가) |
| 3 | `.agent/rules/` | 워크스페이스 수준 보조 규칙 |

- 전역 규칙: `~/.gemini/GEMINI.md`
- 4가지 활성화 모드:

| 모드 | 동작 |
|------|------|
| **Always On** | 항상 적용 |
| **Manual** | `@` 멘션으로 수동 활성화 |
| **Model Decision** | 모델이 자연어 설명을 보고 자동 판단 |
| **Glob** | 파일 패턴 매칭 (예: `*.ts`, `src/**/*.py`) |

### C.3 Skills 실습

- `.agents/skills/`에 `SKILL.md`를 배치한다
- 스킬은 **온디맨드 로드** — Rules와 달리 항상 활성화되지 않고, 에이전트가 관련 작업을 판단할 때만 로드됨

### C.4 MCP 서버 연결

- Antigravity는 MCP를 지원하며, 1,000개 이상의 공식/커뮤니티 MCP 서버를 사용할 수 있다
- [antigravity.codes](https://antigravity.codes/)에서 커뮤니티 MCP 서버 1,500개 이상 탐색 가능

### C.5 Multi-Agent (Manager View)

- Antigravity만의 고유 기능이다
- **Manager View**에서 다수의 에이전트를 동시 생성하고, 각각에 서로 다른 작업을 배정한 뒤 병렬 실행할 수 있다
- 다수의 에이전트를 GUI에서 동시 관리하는 점이 특징이다

### C.6 Browser Integration

- Chrome 확장으로 에이전트가 **웹 애플리케이션을 직접 조작**할 수 있다
- Playwright MCP와 유사한 기능이지만 IDE에 내장되어 있다는 점이 다르다

### C.7 Antigravity 부록의 의도

- 핵심 대응 관계:
  - `copilot-instructions.md` ↔ `GEMINI.md` + `AGENTS.md` + `.agent/rules/`
  - GitHub Copilot Skills ↔ Antigravity Skills (온디맨드 로드)
  - Copilot MCP ↔ Antigravity MCP (동일 프로토콜)
  - 없음 ↔ Manager View (GUI 다중 에이전트)
  - 없음 ↔ Browser Integration (Antigravity만의 강점)

---

## 참고 자료

### GitHub Copilot

- GitHub Copilot agent mode: https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-your-ide
- VS Code MCP 서버 설정: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- GitHub MCP and coding agent: https://docs.github.com/en/copilot/concepts/agents/coding-agent/mcp-and-coding-agent
- GitHub Agent Skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- GitHub custom instructions: https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot

### Playwright MCP

- Playwright MCP GitHub: https://github.com/microsoft/playwright-mcp
- Playwright MCP 공식 문서: https://playwright.dev/docs/getting-started-mcp
- @playwright/mcp npm: https://www.npmjs.com/package/@playwright/mcp

### Skills / Agent Skills

- Agent Skills 오픈 표준: https://agentskills.io
- GitHub Agent Skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- GitHub Agent Skills 만들기: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills

### OpenAI / Codex

- OpenAI MCP docs: https://developers.openai.com/api/docs/mcp
- Apps in ChatGPT: https://help.openai.com/en/articles/11487775-connectors-in-chatgpt
- Codex Skills: https://developers.openai.com/codex/skills/
- Codex Rules: https://developers.openai.com/codex/rules/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md

### Gemini CLI

- Gemini CLI GitHub: https://github.com/google-gemini/gemini-cli
- Gemini CLI MCP 서버 설정: https://geminicli.com/docs/tools/mcp-server/
- Gemini CLI Skills: https://geminicli.com/docs/cli/skills/
- Gemini CLI Extensions: https://geminicli.com/docs/extensions/

### Google Antigravity

- Antigravity 공식 사이트: https://antigravity.google
- Antigravity MCP 문서: https://antigravity.google/docs/mcp
- Antigravity Skills 문서: https://antigravity.google/docs/skills

---

## 다음 주 예고

- 4주차에서는 MCP 서버를 더 실전적으로 다룬다
- 인증, 실패 처리, 로깅, 테스트 가능한 구조를 갖춘 서버 설계로 발전시킨다
- 단순 연결에서 끝나지 않고, 실제 운영 가능한 도구 계층을 만드는 방향으로 확장한다
