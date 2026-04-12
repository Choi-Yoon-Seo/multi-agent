# Week 10. 멀티에이전트 시스템: 고전 원리와 에이전틱 엔지니어링 실습

> 학부 운영안 기준 재구성본
> 기존 원리: 멀티에이전트 기본 구조, 역할 분리, 검증 루프
> 최신 참고 영상: 실밸개발자, 「메타 엔지니어가 알려주는 에이전틱 엔지니어링 핵심 개념 5가지 총정리」, 2026-03-14
> 실습 도구: GitHub Copilot cloud agent, Google Antigravity Agent Manager

https://www.youtube.com/watch?v=m99Vs94oHTQ 

---

## 강의안 개편 계획

이번 주 강의는 기존 10장의 고전적 멀티에이전트 원리를 유지하면서, 최근 개발 도구에서 나타나는 에이전틱 엔지니어링 개념을 실습으로 연결한다. 핵심은 “여러 에이전트를 쓰는 것이 좋은가”가 아니라 “어떤 작업을 어떤 단위로 나누고, 어떤 검증 절차로 통제할 것인가”이다.

### 1단계. 고전 원리 정리

- 단일 에이전트와 멀티에이전트의 차이를 비교한다.
- 계층형, 협력형, 순차형 구조를 구분한다.
- 멀티에이전트를 쓰지 말아야 하는 조건을 함께 다룬다.

### 2단계. 최신 개념 연결

- Agent와 Sub-Agent를 역할 위임 구조로 해석한다.
- Context Engineering을 단순 프롬프트 작성이 아니라 작업 환경 설계로 설명한다.
- Tool, Plugin, MCP를 에이전트가 외부 세계와 연결되는 통로로 다룬다.
- Hook과 Skill을 검증 절차와 재사용 가능한 작업 지식으로 정리한다.
- Planning과 Human-in-the-Loop를 안전한 위임의 조건으로 둔다.

### 3단계. 메뉴 기반 실습

- GitHub에서는 이슈를 에이전트에게 위임하고, 계획, 브랜치, 변경 사항, 풀 리퀘스트를 검토한다.
- Antigravity에서는 Agent Manager에서 여러 작업을 동시에 관리하고, Task Group, 변경 검토, 소스 제어 흐름을 확인한다.
- 두 도구 모두 “자동 생성”보다 “계획 확인, 변경 검토, 테스트 확인”을 중심에 둔다.

---

## 학습 목표

- 멀티에이전트가 필요한 상황과 불필요한 상황을 구분한다.
- Agent, Sub-Agent, Context, Tool, MCP, Hook, Skill, Human-in-the-Loop의 관계를 설명한다.
- GitHub에서 이슈 기반 에이전트 위임 과정을 설계한다.
- Antigravity Agent Manager에서 병렬 작업과 변경 검토 흐름을 실습한다.
- 에이전트 산출물을 그대로 수용하지 않고, 계획, diff, 테스트 결과를 근거로 평가한다.

---

## 이번 주 운영 원칙

- 프레임워크를 많이 외우는 수업이 아니다.
- 멀티에이전트 구현 자체보다 역할 분리와 검증 절차를 우선한다.
- 실습은 작은 저장소와 작은 이슈를 사용한다.
- 자동화 범위는 학생이 직접 설명할 수 있는 수준으로 제한한다.
- 에이전트가 만든 코드는 반드시 사람이 검토한다.

### 필수 범위

- 단일 에이전트와 멀티에이전트 비교
- 계층형, 협력형, 순차형 패턴
- 에이전틱 엔지니어링 5개 축
- GitHub 이슈 기반 위임 실습
- Antigravity Agent Manager 실습

### 심화 범위

- MCP 서버 연결
- Hook을 이용한 사전·사후 검증
- Skill 문서화
- 병렬 에이전트 운영
- 조직 단위 에이전트 정책

---

## 10.1 왜 멀티에이전트인가

하나의 에이전트가 모든 일을 맡으면 역할이 섞이고, 컨텍스트가 커지며, 검증이 약해질 수 있다. 작업이 길어질수록 문제는 더 커진다. 계획, 구현, 테스트, 문서화, 리뷰가 한 대화 안에 섞이면 모델은 중요한 제약을 놓치기 쉽다.

멀티에이전트는 이 문제를 역할 분리로 다룬다.

| 역할 | 책임 | 산출물 |
|---|---|---|
| 계획자 | 작업 범위와 순서 설계 | 구현 계획 |
| 구현자 | 코드 수정 | 변경 파일 |
| 검토자 | 오류, 테스트, 보안 점검 | 리뷰 의견 |
| 문서 담당 | 변경 이유와 사용법 정리 | README 또는 PR 설명 |

다만 역할을 나누면 조정 비용이 생긴다. 작은 함수 하나를 고치는 일에는 멀티에이전트가 오히려 느리고 복잡하다.

---

## 10.2 단일 에이전트와 멀티에이전트 비교

| 항목 | 단일 에이전트 | 멀티에이전트 |
|---|---|---|
| 구조 | 단순하다 | 복잡하다 |
| 구현 비용 | 낮다 | 높다 |
| 역할 분리 | 약하다 | 강하다 |
| 검증 루프 | 사용자가 직접 챙겨야 한다 | 검토 역할을 별도로 둘 수 있다 |
| 추적 가능성 | 대화 흐름에 의존한다 | 계획, 브랜치, PR, 로그로 남길 수 있다 |
| 적합한 작업 | 작은 수정, 단순 자동화 | 복합 기능, 테스트 보강, 문서 동시 수정 |

판단 기준은 다음과 같다.

- 작업을 2개 이상의 독립 단계로 설명할 수 있는가
- 각 단계의 입력과 출력이 분명한가
- 실패했을 때 어느 단계에서 실패했는지 추적할 수 있는가
- 사람의 승인 지점이 필요한가
- 비용과 시간이 증가해도 품질 이득이 있는가

---

## 10.3 기본 패턴

### 계층형

관리자 에이전트가 전체 목표를 이해하고 하위 에이전트에게 작업을 나누어 맡긴다. GitHub의 이슈 위임, Antigravity의 Agent Manager, Claude Code의 Sub-Agent 운영은 모두 이 구조로 해석할 수 있다.

예:

```text
관리자
  ├─ 코드 분석 에이전트
  ├─ 구현 에이전트
  └─ 테스트 에이전트
```

### 협력형

여러 에이전트가 같은 목표를 향해 병렬로 작업한다. 병렬 처리가 가능하다는 장점이 있지만, 충돌 관리가 필요하다.

예:

```text
문서 에이전트  ─┐
테스트 에이전트 ├─ 최종 검토
리팩터링 에이전트 ┘
```

### 순차형

한 에이전트의 산출물이 다음 에이전트의 입력이 된다. 학부 실습에는 순차형이 가장 안전하다.

예:

```text
요구사항 분석 → 구현 계획 → 코드 수정 → 테스트 → PR 설명 작성
```

---

## 10.4 최신 에이전틱 엔지니어링 5개 축

영상은 멀티에이전트를 독립된 유행어가 아니라 에이전틱 엔지니어링의 한 부분으로 다룬다. 수업에서는 다음 5개 축으로 정리한다.

### 1. Agent와 Sub-Agent

Agent는 목표를 받아 계획하고 도구를 사용해 결과를 만든다. Sub-Agent는 특정 역할만 맡는 하위 작업자이다. 핵심은 “여러 모델을 부른다”가 아니라 “책임을 분명히 나눈다”에 있다.

수업 적용:

- 분석 담당: 코드 구조와 문제 원인 조사
- 구현 담당: 최소 변경으로 코드 수정
- 검토 담당: 테스트, 보안, 회귀 위험 점검

### 2. Context Engineering

프롬프트는 한 번 입력하는 지시문이다. Context Engineering은 에이전트가 볼 자료, 규칙, 파일, 도구, 제약을 설계하는 일이다. 좋은 컨텍스트는 긴 설명보다 중요한 자료를 정확히 제공한다.

수업 적용:

- 이슈 본문에 목표, 범위, 제외 범위를 쓴다.
- 저장소에 `README.md`, 테스트 실행법, 코딩 규칙을 남긴다.
- 에이전트에게 “전체 리팩터링 금지”, “테스트를 먼저 확인” 같은 제약을 준다.

### 3. Tool, Plugin, MCP

도구는 에이전트가 실제 행동을 하게 만드는 통로이다. GitHub에서는 이슈, 브랜치, PR, Actions가 도구 환경이다. Antigravity에서는 에디터, 터미널, 브라우저, Source Control, Agent Manager가 도구 환경이다. MCP는 외부 도구와 데이터를 연결하는 표준화된 방식으로 이해한다.

수업 적용:

- 도구 권한은 최소화한다.
- 삭제, 배포, 결제, 외부 API 호출은 승인 단계를 둔다.
- 도구 실행 결과를 산출물에 포함시킨다.

### 4. Hook과 Skill

Hook은 특정 시점에 실행되는 검증 또는 자동화 규칙이다. Skill은 반복되는 작업 지식을 재사용 가능한 문서나 절차로 만든 것이다.

수업 적용:

- 변경 전: 작업 계획을 먼저 작성하게 한다.
- 변경 후: 테스트 실행 결과를 요구한다.
- PR 작성 전: 변경 파일, 검증 결과, 남은 위험을 요약하게 한다.

### 5. Planning과 Human-in-the-Loop

Planning은 작업을 작은 단계로 나누는 절차이다. Human-in-the-Loop는 사람이 승인하고 수정 방향을 주는 절차이다. 멀티에이전트가 안전하려면 자동 실행보다 승인 지점을 더 잘 설계해야 한다.

수업 적용:

- 계획 승인 전에는 코드 수정을 허용하지 않는다.
- 테스트 실패 시 자동 재시도보다 원인 설명을 요구한다.
- 최종 병합은 사람이 한다.

---

## 10.5 GitHub 실습: 이슈를 에이전트에게 위임하기

GitHub Copilot cloud agent는 저장소를 조사하고, 구현 계획을 만들고, 브랜치에서 코드를 수정하며, 필요하면 풀 리퀘스트를 만든다. GitHub 문서에 따르면 이 기능은 GitHub Actions 기반의 임시 개발 환경에서 작업하고, 사용자는 변경 사항을 검토하고 반복할 수 있다.

### 준비물

- GitHub 계정
- Copilot 사용 가능 계정 또는 수업 시연 계정
- 작은 실습 저장소
- 테스트 명령이 있는 프로젝트

수업용 저장소는 다음 조건을 만족해야 한다.

- 파일 수가 많지 않다.
- 실패를 확인할 수 있는 테스트가 있다.
- README에 실행 방법이 적혀 있다.
- 실습 전 브랜치 상태가 깨끗하다.

### 실습 시나리오

작은 Python 또는 JavaScript 프로젝트에서 다음 이슈를 만든다.

```markdown
Title: Add input validation and tests for the calculator function

Goal:
The calculator currently accepts invalid input silently.
Add validation so non-numeric input raises a clear error.

Scope:
- Update only the calculator function and its tests.
- Do not rewrite the project structure.
- Keep the public function name unchanged.

Validation:
- Add at least two tests for invalid input.
- Run the existing test command.
- Summarize changed files and remaining risks.
```

### 메뉴 흐름

1. GitHub 저장소에서 Issues 메뉴를 연다.
2. New issue를 선택한다.
3. 위 실습 시나리오를 이슈 본문에 붙여 넣는다.
4. Assignees에서 Copilot 또는 사용 가능한 coding agent를 선택한다.
5. 에이전트가 제안한 계획을 확인한다.
6. 계획이 과하면 “범위를 calculator와 tests로 제한하라”고 댓글을 단다.
7. 에이전트가 만든 브랜치와 변경 사항을 확인한다.
8. Pull request가 만들어졌다면 Files changed 탭에서 diff를 검토한다.
9. 테스트 결과가 없으면 “테스트 명령과 결과를 제시하라”고 요청한다.
10. 문제가 없을 때만 사람이 병합한다.

### 관찰 포인트

| 관찰 항목 | 확인 질문 |
|---|---|
| 계획 | 작업을 작은 단계로 나누었는가 |
| 컨텍스트 | 이슈의 제약을 지켰는가 |
| 변경 범위 | 관련 없는 파일을 건드리지 않았는가 |
| 테스트 | 실패 사례와 정상 사례를 모두 확인했는가 |
| PR 설명 | 변경 이유, 검증 결과, 위험이 드러나는가 |

### 학생 기록 양식

```markdown
## GitHub 에이전트 실습 기록

- 저장소:
- 이슈 제목:
- 에이전트에게 준 역할:
- 에이전트가 만든 계획 요약:
- 변경 파일:
- 테스트 명령:
- 테스트 결과:
- 사람이 수정하거나 지시를 바꾼 부분:
- 단일 에이전트로 충분했는지에 대한 판단:
```

---

## 10.6 Antigravity 실습: Agent Manager에서 멀티에이전트 흐름 보기

Google Antigravity는 agent-first 개발 플랫폼을 표방하며, Agent Manager를 통해 여러 워크스페이스와 여러 에이전트 작업을 한 화면에서 관리한다. 공식 문서에 따르면 Editor와 Agent Manager는 `Cmd+E` 또는 `Ctrl+E`로 전환할 수 있고, Agent Manager에서는 여러 에이전트 작업, Task Group, 변경 검토, Source Control 흐름을 볼 수 있다.

### 준비물

- Google Antigravity 설치
- Git으로 관리되는 작은 프로젝트
- 실행 가능한 테스트 명령
- GitHub 원격 저장소

### 실습 전 안전 설정

- 실습 전 새 브랜치를 만든다.
- 삭제, 설치, 배포, 외부 API 호출은 자동 승인하지 않는다.
- 터미널 명령은 실행 전 확인한다.
- 작업 대상 폴더가 맞는지 확인한다.

### 실습 시나리오

Antigravity Agent Manager에서 다음 작업을 요청한다.

```text
이 저장소의 calculator 기능을 개선한다.

역할 분리:
1. 먼저 구현 계획을 작성한다.
2. 입력 검증 로직을 최소 변경으로 추가한다.
3. 잘못된 입력에 대한 테스트를 추가한다.
4. 변경 파일과 테스트 결과를 요약한다.

제약:
- 관련 없는 파일은 수정하지 않는다.
- 프로젝트 구조를 바꾸지 않는다.
- 테스트 명령을 실행하기 전 나에게 승인을 요청한다.
```

### 메뉴 흐름

1. Antigravity에서 실습 프로젝트 폴더를 연다.
2. 상단 메뉴 또는 단축키로 Agent Manager를 연다.
3. 새 작업을 만들고 실습 시나리오를 입력한다.
4. Planning Mode 또는 계획 생성 단계를 확인한다.
5. Task Group이 생성되면 하위 작업이 어떻게 나뉘었는지 본다.
6. 터미널 명령 승인 요청이 나오면 명령의 목적을 확인한다.
7. 변경이 끝나면 Review Changes 패널을 연다.
8. 변경 파일을 하나씩 확인하고 주석을 단다.
9. Source Control 탭에서 stage 여부와 커밋 메시지를 검토한다.
10. GitHub에 push한 뒤 PR을 만들거나, 수업에서는 diff 캡처만 제출한다.

### 관찰 포인트

| Antigravity 화면 | 멀티에이전트 개념 |
|---|---|
| Agent Manager | 계층형 관리자 관점 |
| Task Group | 작업 분해와 병렬 처리 |
| Progress updates | 에이전트 행동 로그 |
| Pending steps | Human-in-the-Loop 승인 지점 |
| Review Changes | 사후 검증 |
| Source Control | 산출물 확정과 기록 |

### 학생 기록 양식

```markdown
## Antigravity 에이전트 실습 기록

- 프로젝트:
- 요청한 작업:
- Task Group 개수:
- 하위 작업 요약:
- 승인한 터미널 명령:
- 변경 파일:
- 테스트 결과:
- Review Changes에서 발견한 문제:
- GitHub 실습과 비교한 차이:
```

---

## 10.7 두 실습의 비교

| 항목 | GitHub 중심 실습 | Antigravity 중심 실습 |
|---|---|---|
| 시작점 | Issue 또는 PR | Agent Manager 또는 Editor |
| 작업 위치 | GitHub Actions 기반 임시 환경 | 로컬 워크스페이스 |
| 강점 | 이슈, 브랜치, PR 기록이 분명하다 | 에디터, 터미널, 브라우저를 함께 다룬다 |
| 위험 | 이슈 설명이 약하면 범위가 흔들린다 | 로컬 파일과 터미널 권한 관리가 중요하다 |
| 검증 지점 | PR diff, Actions, 리뷰 | Review Changes, 테스트 실행, Source Control |
| 수업 초점 | 협업 기록과 PR 검토 | Agent Manager와 Task Group 이해 |

정리하면 GitHub 실습은 팀 협업과 기록에 강하고, Antigravity 실습은 작업 진행 상황과 로컬 개발 흐름을 관찰하기 좋다. 두 방식 모두 멀티에이전트의 핵심을 “역할 분리와 검증”으로 이해해야 한다.

---

## 10.8 언제 멀티에이전트를 쓰지 말아야 하는가

다음 경우에는 단일 에이전트가 더 낫다.

- 작업이 10분 안에 끝나는 작은 수정이다.
- 변경 파일이 1개뿐이고 테스트도 단순하다.
- 역할을 나누어도 입력과 출력이 분명하지 않다.
- 에이전트가 사용할 도구 권한을 통제하기 어렵다.
- 팀이 아직 Git, 테스트, PR 리뷰 절차에 익숙하지 않다.

멀티에이전트는 복잡한 작업을 통제하기 위한 수단이다. 복잡하지 않은 일을 복잡하게 만드는 방식으로 쓰면 학습 효과가 떨어진다.

---

## 10.9 활동: 에이전트 작업 설계표 작성

### 목표

학생은 하나의 개발 과제를 골라 단일 에이전트 방식과 멀티에이전트 방식을 비교한다.

### 활동 방법

1. 작은 기능 개선 또는 버그 수정 과제를 고른다.
2. 단일 에이전트에게 줄 프롬프트를 작성한다.
3. 멀티에이전트 방식으로 역할을 2개 또는 3개로 나눈다.
4. 각 역할의 입력, 출력, 검증 기준을 적는다.
5. GitHub 또는 Antigravity 중 하나를 골라 실제 실습을 진행한다.

### 설계표

| 구분 | 내용 |
|---|---|
| 과제명 |  |
| 단일 에이전트 프롬프트 |  |
| 역할 1 | 입력 / 작업 / 출력 |
| 역할 2 | 입력 / 작업 / 출력 |
| 역할 3 | 입력 / 작업 / 출력 |
| 사람 승인 지점 |  |
| 테스트 명령 |  |
| 성공 기준 |  |
| 멀티에이전트가 필요한 이유 |  |

---

## 10.10 제출물

### 필수 제출

- 에이전트 작업 설계표 1개
- GitHub 또는 Antigravity 실습 기록 1개
- 변경 전후 diff 또는 PR 링크
- 테스트 결과 캡처 또는 로그
- 5문장 회고

### 회고 질문

1. 에이전트가 계획을 잘 나누었는가
2. 사용자가 준 제약을 지켰는가
3. 사람이 개입한 지점은 어디였는가
4. 멀티에이전트 방식이 단일 에이전트보다 나았는가
5. 다음 실습에서 컨텍스트를 어떻게 개선할 것인가

---

## 체크리스트

- 단일 에이전트와 멀티에이전트의 차이를 설명할 수 있다.
- 계층형, 협력형, 순차형 패턴을 예로 설명할 수 있다.
- Agent와 Sub-Agent의 관계를 설명할 수 있다.
- Context Engineering이 프롬프트 작성과 어떻게 다른지 설명할 수 있다.
- Tool, MCP, Hook, Skill의 역할을 구분할 수 있다.
- GitHub에서 이슈 기반 에이전트 위임 흐름을 설명할 수 있다.
- Antigravity Agent Manager에서 Task Group과 Review Changes를 확인할 수 있다.
- 에이전트 산출물을 테스트와 diff로 검증할 수 있다.

---

## 참고 자료

- YouTube: https://www.youtube.com/watch?v=m99Vs94oHTQ
- GitHub Docs, About GitHub Copilot cloud agent: https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/coding-agent/about-coding-agent
- Google Antigravity: https://antigravity.google/
- Google Antigravity Docs: https://antigravity.google/docs
- Google Antigravity Agent Manager: https://antigravity.google/docs/agent-manager
- Google Antigravity Task Groups: https://antigravity.google/docs/task-groups
- Google Antigravity Review Changes + Source Control: https://antigravity.google/docs/review-changes-manager

---

## 다음 주 예고

다음 주에는 에이전트 산출물의 환각, 테스트 실패, 보안 위험, 품질 게이트를 다룬다. 이번 주의 Human-in-the-Loop 개념은 다음 주 검증 전략의 출발점이 된다.
