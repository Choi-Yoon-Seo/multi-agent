# Week 11. 에이전틱 엔지니어링 실습 2: 코딩 에이전트 (도구 중립)

> 강의 + 수업 위임 실습 + Homework 위임 과제
> **도구는 학생이 가진 것 중에서 고른다.** 다음 셋 중 하나를 사용한다.
> 트랙 A — **GitHub Copilot cloud agent** (이슈 → PR 위임)
> 트랙 B — **Google Antigravity Agent Manager** (로컬 IDE)
> 트랙 C — **Claude Code** (CLI/IDE)

---

## 학습 목표

- 에이전틱 엔지니어링의 5축(Agent·Sub-Agent / Context Engineering / Tool·MCP / Hook·Skill / Planning·HITL)을 자기 작업 위에서 설명한다
- 어떤 도구를 쓰든 **공통 6단계 워크플로**(Context → Plan → Plan 검토 → 실행 → 검증 → 반영)를 따른다
- 자신이 고른 도구의 메뉴를 “계획 검토”와 “결과 검토” 두 HITL 지점에 매핑한다
- 10주차의 LangGraph Supervisor와의 *동일성과 차이*를 설명한다

---

## 이번 주 핵심 원칙

- 수업의 핵심은 *도구*가 아니라 **검증 가능한 위임 절차**다
- 도구가 달라도 제출 양식·관찰 표·회고 질문은 같다
- 자동 병합(auto-merge) / 자동 적용 금지 — 어떤 도구든 사람이 두 번 검토한다
- 작은 저장소·작은 작업으로 시작한다

---

## 11.1 에이전틱 엔지니어링 5축 (도구 무관)

“프롬프트 잘 쓰는 기술”에서 “**에이전트가 일할 환경 전체를 설계하는 기술**”로 옮겨가는 흐름이다.

### 축 1. Agent와 Sub-Agent

- **Agent**: 목표를 받아 계획하고 도구를 써서 결과를 만든다
- **Sub-Agent**: 특정 역할만 맡는 하위 작업자

10주차 LangGraph의 `researcher / analyst / writer`가 이미 Sub-Agent였다. 코딩 에이전트도 내부적으로 “계획자 + 구현자 + 검토자”를 가진 Sub-Agent 구조로 동작한다.

### 축 2. Context Engineering

프롬프트 한 줄이 아니라, **에이전트가 읽을 자료·규칙·파일·도구·제약** 전체를 설계하는 일이다.

| 컨텍스트 요소 | 이번 실습에서의 형태 |
|---|---|
| 목표 | 작업 정의서의 “Goal” |
| 범위·제외 범위 | 작업 정의서의 “Scope” |
| 검증 기준 | 작업 정의서의 “Validation” |
| 코딩 규칙 | `README.md`, `CONTRIBUTING.md`, `CLAUDE.md` 등 |
| 도구 환경 | git, 테스트 명령, MCP 서버 |

좋은 컨텍스트는 *길지 않다*. **중요한 자료를 정확히** 제공한다.

### 축 3. Tool, Plugin, MCP

도구는 에이전트가 실제 행동하는 통로다.

- 공통 도구: 파일 시스템, git, 테스트 명령
- 트랙 A 추가: GitHub 이슈·PR·Actions
- 트랙 B 추가: Antigravity Editor·Browser·Terminal·Source Control
- 트랙 C 추가: Claude Code의 Skills·Hooks·MCP servers

수업 적용 원칙:
- 권한은 **최소화**한다
- 삭제·배포·결제·외부 API 호출은 *반드시 승인 단계*를 둔다
- 도구 실행 결과는 산출물에 포함한다

### 축 4. Hook과 Skill

- **Hook**: 특정 시점에 자동 실행되는 검증/규칙
- **Skill**: 반복 작업 지식을 재사용 가능한 절차로 정리한 것

| 도구 | Hook의 형태 | Skill의 형태 |
|---|---|---|
| GitHub | Actions의 PR 트리거 워크플로우 | `.github/ISSUE_TEMPLATE`, `PULL_REQUEST_TEMPLATE.md` |
| Antigravity | Pre/Post action 승인 게이트 | Task Group 템플릿 |
| Claude Code | `settings.json`의 hooks | `.claude/skills/*.md`, `CLAUDE.md` 메모리 |

같은 *개념*이 도구마다 다른 *이름*으로 나타난다.

### 축 5. Planning과 Human-in-the-Loop

- **Planning**: 에이전트가 코드를 만지기 전에 *계획을 먼저 출력*한다
- **HITL**: 사람이 계획·diff·테스트 결과를 보고 *승인*한다

세 도구 모두 이 두 단계를 명시적으로 분리한다 (방식만 다르다).

---

## 11.2 공통 6단계 워크플로

도구가 무엇이든 다음 6단계를 따른다.

```text
[1] Context 정의 ──── 작업 정의서: Goal / Scope / Validation
        │
        ▼
[2] Plan 받기 ─────── 에이전트가 계획을 먼저 출력
        │
        ▼
[3] Plan 검토 ───────  ← HITL 게이트 1 (사람이 계획을 본다)
        │
        ▼
[4] 실행 ──────────── 에이전트가 코드 수정·테스트 실행
        │
        ▼
[5] diff·테스트 검토 ←  HITL 게이트 2 (사람이 결과를 본다)
        │
        ▼
[6] 반영/병합 ──────── 사람이 최종 결정
```

**모든 도구에서 게이트 1과 게이트 2를 *건너뛰지 않는다.*** 이게 이번 주 평가의 핵심이다.

---

## 11.3 작업 정의서 (공통 양식)

어떤 트랙이든 다음 양식으로 작업을 정의한다. 이 문서가 Context Engineering의 본체다.

```markdown
## Goal
(무엇을 해야 하는가, 한 문장)

## Scope
- 수정 가능한 파일:
- 수정 금지 파일:
- 변경 금지 사항:

## Validation
- [ ] 새 테스트가 추가되었다
- [ ] 기존 테스트가 모두 통과한다
- [ ] 결과 보고에 변경 파일·테스트 결과·남은 위험이 정리되어 있다
```

### 예시 작업

```markdown
## Goal
calculator.core.add 함수가 숫자가 아닌 입력을 받으면 명확한 오류를 던지게 한다.

## Scope
- 수정 가능한 파일: calculator/core.py, tests/test_core.py
- 수정 금지 파일: README.md, requirements.txt
- 변경 금지 사항: add 함수의 이름과 시그니처(현재: add(a, b))

## Validation
- [ ] 잘못된 입력에 대한 테스트가 최소 2개 추가되었다
- [ ] 기존 add(2, 3) == 5 테스트는 그대로 통과한다
- [ ] 결과 보고에 변경 파일·테스트 결과·남은 위험이 정리되어 있다
```

---

## 11.4 실습 시나리오 — 트랙별 메뉴

학생은 자신이 가진 도구 한 가지를 골라 진행한다. **세 트랙 모두 같은 작업 정의서**를 사용한다.

이번 주 실습도 별도 `practice/chapter11` 폴더를 만들지 않는다. 저장소 루트에서 열고, 실제 수정 대상은 9~13주차 통합 실습 폴더인 `multi-agent/`로 둔다.

### 트랙 A. GitHub Copilot cloud agent

> 사전 조건: GitHub 계정 + Copilot 코딩 에이전트 활성화 (조직 또는 GitHub Education 계정)
> 비동기. 결과를 기다린다.

#### 메뉴 흐름

1. 저장소에 위 작업 정의서를 본문으로 한 **이슈**를 만든다
2. 이슈 우측 **Assignees**에서 “Copilot”을 선택한다
3. 수 분 내에 Copilot이 **계획 댓글**을 단다 → **게이트 1**: 사람이 계획을 검토하고 댓글로 수정 지시
4. Copilot이 브랜치를 만들고 코드 수정 + 테스트 실행 + **PR 생성**
5. PR의 **Files changed / Checks / 본문**을 검토 → **게이트 2**
6. 문제가 있으면 PR 댓글로 추가 지시, 통과하면 사람이 **Squash and merge** (auto-merge 금지)

#### 결정적 화면

- 계획 댓글 (게이트 1)
- PR Files changed 탭
- PR Checks 탭 (Actions 결과)
- PR 본문의 변경 파일·테스트 결과·남은 위험

---

### 트랙 B. Google Antigravity Agent Manager

> 사전 조건: Antigravity 설치 + Git으로 관리되는 작은 프로젝트 (`multi-agent/` 사용)
> 동기·로컬. 터미널 명령은 *반드시* 사전 승인.

#### 메뉴 흐름

1. Antigravity에서 저장소 루트를 열고 `multi-agent/`를 실습 대상으로 지정한다
2. `Cmd+E` / `Ctrl+E`로 **Agent Manager**를 연다
3. 새 작업을 만들고 **작업 정의서를 그대로 입력**한다 (제약 부분 강조)
4. **Planning Mode** 또는 계획 생성 단계 표시 → **게이트 1**: 계획·Task Group을 검토
5. 터미널 명령 승인 요청이 나오면 **명령의 목적**을 확인하고 승인 (삭제·설치는 거절)
6. 변경이 끝나면 **Review Changes** 패널에서 파일별 검토 → **게이트 2**
7. **Source Control** 탭에서 stage·커밋 메시지를 검토하고 사람이 커밋
8. 필요하면 GitHub로 push 후 PR 생성, 또는 diff 캡처만 제출

#### 결정적 화면

- Agent Manager의 Task Group
- Pending steps (승인 대기)
- Review Changes 패널
- Source Control 탭

---

### 트랙 C. Claude Code

> 사전 조건: Claude Code CLI 또는 IDE 확장 + 작은 저장소 (`multi-agent/` 사용)
> 대화형. **Plan mode**가 핵심.

#### 메뉴 흐름

1. 저장소 루트에서 Claude Code를 연다 (CLI 또는 IDE)
2. 처음 한 번: 저장소 루트에 `CLAUDE.md`를 만들어 코드 규칙·테스트 명령·주의사항을 적는다 (Skill 역할)
3. **Plan mode**로 진입 (CLI: `/plan` 또는 Shift+Tab의 Plan)
4. 작업 정의서를 그대로 프롬프트로 입력한다
5. Claude가 **계획**을 출력 → **게이트 1**: 계획을 읽고, 부족하면 추가 제약을 댓글처럼 추가
6. Plan을 승인하면 Claude가 코드 수정·테스트 실행 (각 Edit·Bash 호출이 사용자 승인을 거친다 — `acceptEdits` 모드는 *이번 실습에서는 끄고* 진행)
7. 변경이 끝나면 `git diff`로 diff 검토, 테스트 결과 확인 → **게이트 2**
8. 사람이 직접 커밋·push, 필요시 PR 생성

#### 결정적 화면

- Plan mode 출력
- 각 Edit/Bash 승인 프롬프트 (게이트 2가 *연속적으로* 발생)
- 최종 `git diff` 출력

#### 주의

- 이번 실습에서는 `bypassPermissions` 절대 금지
- `CLAUDE.md`에 “테스트는 반드시 실행 후 결과 보고” 류의 절차를 적어 두면 매번 다시 지시할 필요가 없다 (Skill의 본체)

---

## 11.5 공통 관찰 표

어떤 트랙이든 다음 표를 채운다. 평가의 기준이 된다.

| 단계 | 관찰 항목 | 사용한 도구 트랙 | 본 것 |
|---|---|---|---|
| Plan | 작업을 하위 단계로 어떻게 나누었는가 |  |  |
| Plan | Scope 제약을 지켰는가 |  |  |
| 실행 | 관련 없는 파일을 건드렸는가 |  |  |
| 실행 | 어떤 명령을 실행했고 결과는 무엇인가 |  |  |
| 검증 | 테스트의 실패·정상 사례가 모두 추가됐는가 |  |  |
| HITL 1 | 계획 단계에서 사람이 개입한 지점·내용 |  |  |
| HITL 2 | 결과 단계에서 사람이 개입한 지점·내용 |  |  |
| 회복 | 잘못된 방향을 어떻게 돌렸는가 |  |  |

---

## 11.6 LangGraph Supervisor와의 비교

세 트랙 모두 같은 비교 표를 채운다.

| 항목 | 10주차 LangGraph Supervisor | 11주차 코딩 에이전트 (선택 트랙) |
|---|---|---|
| 책임 분리 | researcher / analyst / writer | 계획자 / 구현자 / 검토자 (도구 내부) |
| 핸드오프 | `Command(goto=...)` | (트랙에 따라 — 댓글/Task Group/Plan 승인) |
| 컨텍스트 | TypedDict 상태 | 작업 정의서 + 저장소 + (`CLAUDE.md` 등) |
| 도구 | LLM API | 파일 시스템·git·테스트 명령 + 도구별 추가 |
| 검증 | RESEARCH_NEEDED, recursion_limit | (트랙) Actions / Review Changes / `git diff` |
| HITL 지점 | (이번 주는 없음, 13주차에 추가) | Plan 검토, 결과 검토 |
| 추적 | LangSmith 트레이스 | (트랙) 이슈·PR / Source Control / 대화 로그 |

같은 개념이 *프레임워크*에 있느냐 *플랫폼/CLI*에 있느냐 차이다. 본질은 같다.

---

## 11.7 자주 만나는 실수 (트랙 공통)

| 증상 | 원인 | 해결 |
|---|---|---|
| 에이전트가 Scope를 무시한다 | Scope가 모호하다 | 파일 경로·금지 사항을 *문장*이 아니라 *목록*으로 |
| 테스트가 늘었지만 의미가 없다 | Validation 기준이 약하다 | “최소 N개”, “이 케이스 반드시 포함” 같은 강한 제약 |
| 한 번에 너무 큰 변화 | 작업 하나에 여러 목표 | 작업을 쪼갠다 |
| 자동화에 떠밀려 사람 검토가 형식적 | HITL 게이트가 빈약 | 게이트 1·2에서 *반드시 한 줄 이상* 적는다 |
| 사람이 매번 큰 폭으로 수정해야 함 | Context 부족 | `CLAUDE.md` / `README.md` / 이슈 본문을 채운다 |

### 트랙별 함정

| 트랙 | 자주 빠지는 함정 |
|---|---|
| A (Copilot) | 계획 댓글을 안 읽고 PR로 직행 |
| B (Antigravity) | 터미널 명령 승인을 *습관적으로* 누름 (삭제 명령 주의) |
| C (Claude Code) | 매번 Edit 승인이 귀찮아 `acceptEdits` 켜 버림 (수업에서 금지) |

---

## 11.8 활동: 자기 저장소 한 곳을 “에이전트 친화적”으로 만들기

### 목표

수업 실습에서는 `multi-agent/` 안의 작은 예시 작업을 대상으로, 에이전트에게 안전하게 위임하는 과정을 따라 한다.

수업 실습 파일:

```text
multi-agent/docs/week11_inclass_delegation.md
```

Homework에서는 각자 다른 작은 작업을 정해 같은 절차로 위임한다.

```text
multi-agent/docs/week11_homework_delegation.md
```

### 활동 내용 (트랙 무관)

1. `README.md`에 “실행 방법”과 “테스트 방법”을 한 단락으로 정리
2. 작업 정의서 양식(Goal/Scope/Validation)을 저장소에 둔다
   - 트랙 A: `.github/ISSUE_TEMPLATE/agent-task.md`
   - 트랙 B/C: `docs/AGENT_TASK_TEMPLATE.md` 같은 일반 파일
3. 트랙 C 사용자라면 `CLAUDE.md`를 추가해 코드 규칙·테스트 명령·금지 사항을 적는다
4. 작은 실패 테스트를 일부러 하나 두고, 그것을 고치는 작업을 작성
5. 자신이 고른 트랙으로 위임

산출물: 정리된 저장소 + 실습 결과 캡처.

---

## 11.9 제출물 (트랙 무관, 공통 양식)

### 필수

- 수업 실습 파일: `multi-agent/docs/week11_inclass_delegation.md`
- Homework 파일: `multi-agent/docs/week11_homework_delegation.md`
- 실습 저장소 URL
- 사용한 도구 트랙 (A/B/C 중 하나) + 선택 이유 1줄
- 작업 정의서 (Goal/Scope/Validation 채운 본문)
- **계획 단계 캡처** — 트랙 A: 이슈 댓글 / 트랙 B: Task Group / 트랙 C: Plan mode 출력
- **결과 단계 캡처** — 트랙 A: PR Files changed / 트랙 B: Review Changes / 트랙 C: `git diff`
- 테스트 결과 (Actions 또는 로컬 실행)
- 11.5 관찰 표 (채워서)
- 11.6 LangGraph 비교 표 (채워서)
- 5문장 회고

### 회고 질문 (트랙 무관)

1. 계획 단계에서 사람이 어떤 한 줄을 추가했더라면 더 좋았겠는가
2. 결과 단계에서 발견한 가장 큰 문제는 무엇이었는가
3. 10주차의 LangGraph Supervisor와 가장 비슷한 부분과 가장 다른 부분은 무엇인가
4. 다른 트랙(A/B/C 중 안 쓴 두 개)이라면 같은 작업이 어떻게 달라졌겠는가
5. *자동 적용*을 켜지 *않을* 이유는 무엇인가

---

## 체크리스트

- 에이전틱 엔지니어링 5축을 자기 실습 위에서 설명할 수 있다
- 공통 6단계 워크플로(Context → Plan → Plan 검토 → 실행 → 검증 → 반영)를 따랐다
- 자신이 고른 트랙의 메뉴를 게이트 1·2에 매핑했다
- 작업 정의서로 컨텍스트를 설계했다
- HITL 게이트에서 *최소 한 줄 이상*의 사람 개입을 남겼다
- 자동 병합/자동 적용을 켜지 않았다

---

## 참고 자료

### 공통
- Anthropic 「Engineering effective tool descriptions」 (Context Engineering 참고)

### 트랙 A (GitHub Copilot)
- About GitHub Copilot coding agent: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
- 시작하기: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent
- GitHub Education: https://education.github.com/

### 트랙 B (Antigravity)
- Google Antigravity: https://antigravity.google/
- Agent Manager: https://antigravity.google/docs/agent-manager
- Task Groups: https://antigravity.google/docs/task-groups
- Review Changes: https://antigravity.google/docs/review-changes-manager

### 트랙 C (Claude Code)
- Claude Code 공식 문서: https://docs.claude.com/en/docs/claude-code
- Plan mode 안내: 같은 문서의 Permission modes 항목
- Skills·Hooks·MCP servers 가이드: 같은 문서의 해당 섹션

---

## 다음 주 예고

12주차에는 멀티에이전트에 **외부 지식**을 붙인다. 검색 에이전트를 추가해 RAG를 만들고, 답변에 출처를 남기며, 환각을 검증하는 가드레일을 적용한다. 11주차에서 배운 “계획 검토 + 결과 검토”의 두 게이트가 13주차의 `interrupt` 기반 HITL 노드와 어떻게 같은 개념인지도 함께 본다.
