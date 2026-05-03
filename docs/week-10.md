# Week 10. 코딩에이전트 도구 사용법 집중 실습

> 9주차 멀티에이전트 설계 과제를 이어 받아, 11~14주차 일정공지 에이전트 프로젝트를 만들 준비를 한다.  
> 이번 주의 목표는 코드를 많이 짜는 것이 아니라, 코딩에이전트에게 일을 맡기고 결과를 검토하는 기본 절차를 익히는 것이다.

---

## 학습 목표

- GitHub Copilot, Gemini CLI, Antigravity의 작업 방식을 구분한다.
- 같은 작업을 세 도구에 지시해 보고 결과 차이를 비교한다.
- `.github/copilot-instructions.md`, `context.md`, `todo.md`의 역할을 이해한다.
- 9주차 설계 과제를 11주차 프로젝트 시작 문서로 바꾼다.
- 코딩에이전트가 만든 결과를 그대로 믿지 않고, 계획과 변경 내용을 확인한다.

---

## 이번 주 핵심 원칙

1. 새 프로젝트를 시작하지 않는다. 9주차 과제를 이어 쓴다.
2. 세 도구를 깊게 파지 않는다. 공통 작업 흐름을 익힌다.
3. 코드는 최소화한다. 오늘의 산출물은 지시문, 컨텍스트 문서, 작업 기록이다.
4. 자동 적용보다 검토를 우선한다. 계획을 보고, 변경 내용을 보고, 실행 결과를 본다.
5. 11주차부터 만들 일정공지 에이전트의 준비 문서를 만든다.

---

## 10.1 9주차 과제에서 출발하기

9주차 과제는 멀티에이전트 프로젝트의 설계 초안이다. 이번 주에는 그 과제를 실제 개발에 쓸 수 있는 문서로 바꾼다.

| 9주차 과제 항목 | 10주차에서 바꿀 문서 |
|---|---|
| 관심 도메인 | `context.md`의 프로젝트 배경 |
| 단일 에이전트의 한계 | `context.md`의 문제 정의 |
| 역할 분리 | `context.md`의 에이전트 역할 |
| 입력과 출력 | `context.md`의 입출력 명세 |
| 실패 조건 | `todo.md`의 검증 항목 |

11~14주차 공통 프로젝트는 “일정공지 에이전트”이다. 각자 다른 주제를 새로 만들지 않는다. 대신 같은 프로젝트를 만들면서 입력 공지 예시나 사용자 유형을 조금씩 바꿀 수 있다.

---

## 10.2 이번 프로젝트: 일정공지 에이전트

일정공지 에이전트는 여러 공지를 읽고, 날짜와 대상자를 정리한 뒤, 사용자별로 해야 할 일을 안내하는 간단한 멀티에이전트 프로그램이다.

기본 흐름은 다음과 같다.

```text
[공지 입력]
   ↓
[사실 추출 에이전트]
   ↓
[일정 분류 에이전트]
   ↓
[안내문 작성 에이전트]
   ↓
[결과 출력]
```

처음에는 실제 AI 호출을 복잡하게 붙이지 않는다. Python 함수 여러 개를 에이전트 역할처럼 나누고, 코딩에이전트에게 그 구조를 만들게 한다.

---

## 10.3 세 도구의 역할

이번 주에는 세 도구를 모두 한 번씩 사용한다.

| 도구 | 수업에서의 역할 | 강점 | 주의점 |
|---|---|---|---|
| GitHub Copilot | VS Code 안에서 빠르게 코드와 문서 초안 작성 | 접근이 쉽고 편집 흐름이 자연스럽다 | 지시가 넓으면 불필요한 파일을 만들 수 있다 |
| Gemini CLI | 터미널에서 프로젝트 파일을 읽고 작업 | 명령 실행과 파일 단위 작업을 시키기 좋다 | 계획 없이 바로 수정하게 두면 추적이 어렵다 |
| Antigravity | Agent Manager로 작업 단위를 관리 | 여러 단계 작업과 변경 검토가 편하다 | 도구 UI에 익숙해지는 시간이 필요하다 |
| Playwright CLI | 브라우저에서 HTML과 결과 화면을 확인 | 화면 확인과 스크린샷에 좋다 | MCP가 아니라 CLI로만 사용한다 |

중요한 것은 특정 도구의 메뉴를 외우는 것이 아니다. 세 도구 모두 다음 흐름으로 쓴다.

```text
컨텍스트 제공 → 계획 요청 → 계획 검토 → 실행 요청 → 변경 확인 → 실행 검증
```

---

## 10.4 Playwright CLI 설치

이번 수업에서는 Playwright MCP를 붙이지 않는다. 대신 Playwright CLI를 설치해 HTML 자료, README 미리보기, 나중에 만들 간단한 웹 출력 화면을 브라우저에서 확인한다.

공식 Playwright Agent CLI 기준 설치 명령은 다음과 같다.

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install-browser
```

Windows PowerShell에서도 같은 명령을 사용한다.

```powershell
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install-browser
```

설치 확인:

```bash
playwright-cli --help
```

사용 예시는 다음 정도만 다룬다.

```bash
playwright-cli open docs/week-10.html
```

브라우저가 열리면 성공이다. 이번 주에는 자동 테스트 코드를 만들지 않는다. 목적은 “브라우저 확인을 CLI로 할 수 있다”를 경험하는 것이다.

---

## 10.5 공통 준비 파일

프로젝트 루트에 다음 파일을 만든다.

```text
AGENTS.md
.github/copilot-instructions.md
GEMINI.md
.agents/skills/schedule-agent/SKILL.md
.agents/skills/playwright-check/SKILL.md
context.md
todo.md
week10_tool_practice.md
```

운영 방식은 단순하다.

| 도구 | 자동/수동 사용 방식 |
|---|---|
| GitHub Copilot | VS Code에서는 `AGENTS.md`를 인식할 수 있다. 그래도 `.github/copilot-instructions.md`에서 `AGENTS.md`를 다시 가리키게 둔다 |
| Gemini CLI | `GEMINI.md`를 읽게 하고, 그 안에서 `AGENTS.md`를 공통 규칙으로 지정한다 |
| Antigravity | 프로젝트 루트의 `AGENTS.md`를 읽게 하거나, 첫 요청에서 “먼저 AGENTS.md를 읽어라”라고 지시한다 |

도구를 바꿀 때마다 첫 요청은 다음처럼 통일한다.

```text
먼저 AGENTS.md, context.md, todo.md를 읽어줘.
아직 파일을 수정하지 말고, 오늘 할 작업 계획만 말해줘.
```

### `AGENTS.md`

세 도구가 공통으로 참고할 규칙 파일이다. Copilot, Gemini CLI, Antigravity를 번갈아 쓰더라도 같은 규칙을 유지하기 위해 루트에 둔다.

```markdown
# AGENTS.md

이 파일은 GitHub Copilot, Gemini CLI, Antigravity에서 공통으로 참고할 프로젝트 규칙이다.

## 프로젝트
- 이름: 일정공지 에이전트
- 기본 실행: `python schedule_agent.py`
- 기본 작업 파일: `schedule_agent.py`

## 작업 방식
1. 파일을 수정하기 전에 먼저 계획을 제시한다.
2. 한 번에 많은 파일을 바꾸지 않는다.
3. 오류가 나면 새 기능을 추가하지 말고 오류만 고친다.
4. 변경 후 실행 명령과 확인 결과를 보고한다.

## 금지
- 불필요한 패키지 설치
- API 키 하드코딩
- 복잡한 프레임워크 임의 추가
- Playwright MCP 연결
```

### `.github/copilot-instructions.md`

GitHub Copilot용 연결 파일이다. 공통 규칙을 길게 반복하지 않고 `AGENTS.md`를 읽게 한다.

```markdown
# Copilot Instructions

이 저장소의 공통 작업 규칙은 루트의 `AGENTS.md`에 있다.

작업을 시작할 때 먼저 `AGENTS.md`, `context.md`, `todo.md`를 읽고 따른다.

요약:
- 기본 실행 명령은 `python schedule_agent.py`이다.
- 파일을 수정하기 전에 먼저 계획을 제시한다.
- 한 번에 많은 파일을 바꾸지 않는다.
```

### `GEMINI.md`

Gemini CLI용 연결 파일이다. Gemini CLI는 `GEMINI.md`를 잘 읽으므로, 여기서 `AGENTS.md`를 공통 규칙으로 지정한다.

```markdown
# GEMINI.md

이 저장소의 공통 작업 규칙은 루트의 `AGENTS.md`에 있다.

작업을 시작할 때 먼저 `AGENTS.md`, `context.md`, `todo.md`를 읽고 따른다.

요약:
- 기본 실행 명령은 `python schedule_agent.py`이다.
- 파일을 수정하기 전에 먼저 계획을 제시한다.
- 한 번에 많은 파일을 바꾸지 않는다.
```

---

## 10.6 프로젝트 Skills

이번 수업에서 말하는 skill은 거창한 플러그인이 아니다. 코딩에이전트가 반복해서 참고할 작업 절차 문서이다. 프로젝트에는 두 개만 둔다.

```text
.agents/skills/schedule-agent/SKILL.md
.agents/skills/playwright-check/SKILL.md
```

### Skill 1. 일정공지 에이전트 제작

```markdown
---
name: schedule-agent
description: 일정공지 에이전트의 기능을 만들거나 수정할 때 사용한다.
---

# Schedule Agent Skill

## 목표
공지 텍스트에서 일정 정보를 뽑고, 사용자별 안내문을 만든다.

## 기본 흐름
1. 사실 추출: 제목, 대상, 날짜, 해야 할 일, 준비물을 뽑는다.
2. 일정 분류: 사용자 유형별로 공지를 나눈다.
3. 안내문 작성: 사용자별 해야 할 일을 Markdown으로 쓴다.
4. 검토: 날짜 누락, 대상 불명확, 공지에 없는 단정 표현을 확인한다.

## 작업 원칙
- 먼저 계획을 제시한다.
- `schedule_agent.py` 중심으로 수정한다.
- 외부 패키지는 추가하지 않는다.
- 변경 후 `python schedule_agent.py` 실행 결과를 보고한다.
```

### Skill 2. Playwright 화면 확인

~~~markdown
---
name: playwright-check
description: HTML 자료나 출력 화면을 브라우저로 확인할 때 사용한다.
---

# Playwright Check Skill

## 목표
Playwright CLI로 HTML 또는 로컬 페이지가 열리는지 확인한다.

## 기본 명령
```bash
playwright-cli open docs/week-10.html
```

## 작업 원칙
- Playwright MCP를 설정하지 않는다.
- 브라우저 확인이 필요한 경우에만 사용한다.
- 화면 확인 결과를 한두 문장으로 보고한다.
~~~

---

### `context.md`

코딩에이전트가 읽을 프로젝트 설명서이다.

```markdown
# 일정공지 에이전트 프로젝트

## 목표
여러 학과 공지를 읽고, 대상자와 날짜를 정리한 뒤, 사용자별 해야 할 일을 안내한다.

## 입력
공지 여러 개가 들어 있는 텍스트.

## 출력
공지별 핵심 일정 표와 사용자별 안내문.

## 에이전트 역할
1. 사실 추출 에이전트: 제목, 대상, 날짜, 준비물을 뽑는다.
2. 일정 분류 에이전트: 학년이나 사용자 유형별로 공지를 나눈다.
3. 안내문 작성 에이전트: 사용자가 해야 할 일을 짧게 쓴다.

## 제약
- 처음에는 Python 기본 코드로 만든다.
- 코드는 `schedule_agent.py` 하나에서 시작한다.
- 실행 결과는 터미널에 출력하고, 나중에 `output.md`로 저장한다.
```

### `todo.md`

작업 목록이다. 코딩에이전트에게 “무엇부터 할지”를 알려준다.

```markdown
# Todo

- [ ] sample notices를 정한다.
- [ ] 사실 추출 에이전트 함수를 만든다.
- [ ] 일정 분류 에이전트 함수를 만든다.
- [ ] 안내문 작성 에이전트 함수를 만든다.
- [ ] 전체 흐름을 실행하는 main 함수를 만든다.
- [ ] 결과를 Markdown 표로 출력한다.
- [ ] README에 실행 방법을 쓴다.
```

---

## 10.7 GitHub Copilot 실습

### 목표

Copilot에게 프로젝트 규칙과 컨텍스트를 읽히고, 11주차 개발을 위한 문서 초안을 만들게 한다.

### 절차

1. VS Code에서 프로젝트 루트를 연다.
2. `.github/copilot-instructions.md`를 만든다.
3. `context.md`, `todo.md`를 만든다.
4. Copilot Chat에 다음과 같이 요청한다.

```text
context.md와 todo.md를 읽고, 11주차에 만들 일정공지 에이전트의 개발 순서를 더 쉽게 정리해줘.
코드는 아직 만들지 말고, todo.md를 수업 실습 단계로 다듬어줘.
```

### 확인할 것

| 확인 항목 | 질문 |
|---|---|
| 범위 | Copilot이 일정공지 에이전트 범위를 벗어나지 않았는가 |
| 난이도 | 갑자기 LangGraph, RAG, Docker를 넣지 않았는가 |
| 실행 가능성 | 11주차 90분 안에 시작할 수 있는 순서인가 |

---

## 10.8 Gemini CLI 실습

### 목표

터미널에서 프로젝트 파일을 읽고, 계획을 먼저 받은 뒤 작업을 시키는 습관을 만든다.

### 기본 흐름

```bash
gemini
```

Gemini CLI 안에서 다음과 같이 요청한다.

```text
이 프로젝트의 context.md와 todo.md를 읽어줘.
아직 파일을 수정하지 말고, 일정공지 에이전트를 만들기 위한 5단계 계획만 제시해줘.
각 단계는 수업 초보자가 따라 할 수 있게 짧게 써줘.
```

계획이 적절하면 다음 요청을 한다.

```text
좋아. 이제 todo.md만 수정해줘.
11주차에는 뼈대 만들기, 12주차에는 사실 추출, 13주차에는 사용자별 안내문, 14주차에는 최종 정리로 나누어줘.
```

### 확인할 것

Gemini CLI는 명령 실행이나 파일 수정이 편하다. 대신 바로 수정시키기 전에 반드시 계획을 먼저 받는다.

```text
먼저 계획만 말해줘. 아직 파일을 수정하지 마.
```

이 문장을 자주 사용한다.

---

## 10.9 Antigravity 실습

### 목표

Agent Manager에서 하나의 작업을 만들고, 변경 내용을 검토하는 흐름을 익힌다.

### 절차

1. Antigravity에서 프로젝트 루트를 연다.
2. Agent Manager를 연다.
3. 새 작업을 만든다.
4. 다음 지시를 입력한다.

```text
context.md와 todo.md를 읽고, 일정공지 에이전트 프로젝트를 위한 README 초안을 작성해줘.
아직 코드는 만들지 말고, 프로젝트 목표, 실행 예정 파일, 주차별 개발 계획만 정리해줘.
```

5. 계획 또는 작업 단계를 먼저 확인한다.
6. 변경된 파일을 검토한다.
7. 마음에 들지 않으면 다음처럼 다시 지시한다.

```text
내용이 너무 어렵다. LangGraph, RAG, 배포 내용은 빼고, Python 기본 코드로 만드는 일정공지 에이전트 설명만 남겨줘.
```

---

## 10.10 같은 작업을 세 도구에 시켜 보기

세 도구에 같은 작업을 시킨다.

```text
9주차 멀티에이전트 설계 과제를 바탕으로, 일정공지 에이전트 프로젝트의 context.md 초안을 만들어줘.
초보자가 이해할 수 있게 입력, 출력, 역할 3개, 하지 않을 일을 구분해줘.
```

결과를 비교한다.

| 비교 항목 | Copilot | Gemini CLI | Antigravity |
|---|---|---|---|
| 지시를 잘 지켰는가 |  |  |  |
| 너무 어려운 내용을 넣었는가 |  |  |  |
| 파일 변경을 확인하기 쉬웠는가 |  |  |  |
| 다시 수정시키기 쉬웠는가 |  |  |  |
| 내가 계속 쓸 도구로 적합한가 |  |  |  |

---

## 10.11 수업 활동

90분 수업은 다음 순서로 진행한다.

| 시간 | 활동 |
|---|---|
| 0~10분 | 9주차 과제와 11~14주차 프로젝트 연결 설명 |
| 10~20분 | Playwright CLI 설치와 브라우저 열기 확인 |
| 20~35분 | Copilot 실습: instruction, context, todo 만들기 |
| 35~50분 | Gemini CLI 실습: `GEMINI.md`와 계획 먼저 받기 |
| 50~65분 | 프로젝트 skill 2개 만들기 |
| 65~80분 | Antigravity 실습과 세 도구 결과 비교 |
| 80~90분 | 주 도구 선택, 제출물 정리 |

---

## 10.12 Homework

다음 파일을 제출한다.

```text
.github/copilot-instructions.md
GEMINI.md
.agents/skills/schedule-agent/SKILL.md
.agents/skills/playwright-check/SKILL.md
context.md
todo.md
week10_tool_practice.md
```
---

## 체크리스트

- 9주차 과제 내용을 `context.md`에 반영했다.
- `.github/copilot-instructions.md`를 만들었다.
- 세 도구를 모두 한 번 이상 사용했다.
- 도구별 결과 차이를 기록했다.
- 11주차에 사용할 주 도구를 정했다.

---

과제: 

본인들 깃허브 주소를 제출한다. 

## 다음 주 예고

11주차에는 일정공지 에이전트의 첫 번째 버전을 만든다. LangGraph Supervisor를 어렵게 구현하지 않는다. 먼저 Python 함수 3개로 `사실 추출 → 일정 분류 → 안내문 작성` 흐름을 만들고, 코딩에이전트에게 그 뼈대를 생성하게 한다.
