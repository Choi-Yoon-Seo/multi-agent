# Week 3. MCP, Skills, Plugins 실습 입문

> 원본: `docs/ch3.md`

## 학습 목표

- MCP가 왜 필요한지 한 문장으로 설명할 수 있다
- MCP와 Skills/Instructions의 차이를 구분할 수 있다
- GitHub Copilot에서 MCP를 연결해 실제로 한 번 써 볼 수 있다
- 간단한 규칙 파일과 최소 MCP 서버를 직접 만들어 볼 수 있다

---

## 선수 지식

- 2주차에서 만든 `agenticAI/` 실습 환경
- Python 기초 문법
- 가상환경, `.env`, `output/`, `logs/` 사용법

---

## 3.1 이번 장의 핵심만 먼저

이 장에서 먼저 잡아야 할 핵심은 네 가지다.

1. **MCP는 도구 연결이다.**
2. **Skills / Instructions는 작업 규칙이다.**
3. **Plugin / App / Connector는 제품 안에서 묶어 배포하는 방식이다.**
4. **좋은 실습은 "연결했다"에서 끝나지 않고, 호출 결과와 검증까지 남긴다.**

쉽게 비유하면:

- MCP = 에이전트에게 새 손과 도구를 붙여 주는 것
- Skills / Instructions = 그 손을 어떻게 쓰라고 알려 주는 작업 매뉴얼
- Plugin / App / Connector = 이 기능들을 제품 안에서 설치 가능한 묶음으로 포장한 것

---

## 3.2 왜 MCP만 배우면 부족한가

### 3.2.1 도구를 연결해도 결과가 흔들리는 이유

- 에이전트는 도구가 있어도 언제 써야 할지 잘못 판단할 수 있다
- 출력 위치와 파일 이름이 매번 달라질 수 있다
- 검증 없이 "완료"라고 말할 수 있다
- 위험한 명령을 무심코 시도할 수 있다

즉, **MCP만으로는 "할 수 있는 일"만 늘어난다.**
우리가 원하는 것은 "잘 일하는 방식"까지 갖춘 에이전트다.

### 3.2.2 그래서 필요한 것: 도구 + 규칙

- **MCP**는 무엇을 호출할 수 있는지 정한다
- **Skills / Instructions**는 어떻게 일해야 하는지 정한다

둘을 같이 봐야 실습이 안정된다.

예:

- MCP: GitHub 이슈를 읽을 수 있다
- Instruction: 결과는 `output/`에 저장하고, 검증 항목 3개를 남긴다

---

## 3.3 개념 구분 한 번에 정리

| 개념 | 핵심 질문 | 역할 |
|------|----------|------|
| MCP | 무엇을 호출할 수 있는가 | 도구 연결 |
| Skills / Instructions | 어떻게 일하게 할 것인가 | 작업 규칙 |
| Plugin / App / Connector | 제품에 어떻게 붙일 것인가 | 설치/배포/포장 |
| Hooks | 언제 자동으로 검사할 것인가 | 이벤트 연결 |
| Memory / Spaces | 무엇을 계속 기억하게 할 것인가 | 지속 문맥 |

수업에서는 먼저 아래처럼 단순하게 이해하면 충분하다.

- MCP = 도구 연결
- Skills = 작업 매뉴얼
- Instructions = 기본 규칙
- Hooks = 자동 실행
- Memory = 장기 기억
- Plugin/App/Connector = 제품별 포장 방식

---

## 3.4 MCP 빠른 이해

### 3.4.1 MCP가 해결하는 문제

- AI 도구마다 외부 시스템 연결 방식이 다르면 재사용이 어렵다
- 같은 기능을 제품마다 다시 붙여야 한다
- MCP는 이 연결 방식을 표준화하려는 접근이다

### 3.4.2 이 수업에서는 Tools 중심으로 본다

MCP는 보통 세 가지 요소로 설명된다.

- **Tools**: AI가 호출하는 함수
- **Resources**: AI가 읽는 데이터
- **Prompts**: 재사용 가능한 프롬프트 자산

이번 주차에서는 가장 체감이 쉬운 **Tools** 중심으로 실습한다.

### 3.4.3 로컬 MCP와 원격 MCP

- **로컬(STDIO)**: 내 컴퓨터에서 서버 프로세스를 실행하고 연결
- **원격(Remote)**: 네트워크로 외부 MCP 서버에 접속

입문 실습은 보통 로컬 또는 이미 제공된 서버를 연결해 보는 것부터 시작한다.

### 3.4.4 보안과 권한이 중요한 이유

좋은 MCP 서버는 "많이 할 수 있는 서버"가 아니라 "어디까지 할 수 있는지 분명한 서버"다.

예:

- 파일 읽기는 허용
- 파일 삭제는 금지
- 특정 폴더 밖 접근은 금지

---

## 3.5 실습 전에 꼭 기억할 것

이번 장 실습은 아래 세 질문에 답할 수 있으면 충분하다.

1. 어떤 도구를 연결했는가
2. 실제로 어떤 호출이 일어났는가
3. 결과를 어떻게 검증했는가

실습 결과는 가능하면 아래 네 가지로 남긴다.

- 코드
- 실행 로그
- 출력 파일
- 체크리스트

---

## 3.6 실습 1: 기존 MCP 서버 연결해서 써 보기

### 실습 목표

- GitHub Copilot에서 MCP 서버를 연결하고 실제 호출을 확인한다

### 가장 쉬운 흐름

1. MCP 서버 하나를 고른다
2. Copilot에 등록한다
3. 도구가 실제로 호출되도록 요청한다
4. 입력과 출력을 기록한다
5. 결과를 검증한다

### 권장 시작점

- GitHub MCP server
- 파일 시스템 계열 MCP
- 단순 유틸리티 서버

### GitHub Copilot에서 해 볼 수 있는 방식

- Extensions 뷰에서 `@mcp` 검색
- `.vscode/mcp.json`에 서버 추가
- Command Palette에서 `MCP: Add Server` 실행

예시:

```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

### 요청 예시

```text
현재 저장소와 관련된 최근 열린 이슈를 확인하고,
week3 실습에 도움 될 만한 내용을 요약해줘.
가능하면 MCP 도구를 사용해줘.
```

### 관찰 포인트

- 정말 MCP 도구를 호출했는가
- 어떤 설명이 도구 선택에 영향을 줬는가
- 승인 요청은 언제 나타났는가
- 결과를 그대로 믿으면 위험한 부분은 없는가

### 기록 예시

```markdown
- 호출 도구: read_file
- 입력: path=docs/notes.md
- 결과: 파일 내용 정상 반환
- 검증: 실제 파일과 내용 비교 완료
- 관찰: 경로를 잘못 주면 오류 메시지가 애매했음
```

---

## 3.7 실습 2: 규칙 파일 만들고 전후 비교하기

### 실습 목표

- 같은 작업을 규칙 없이 했을 때와 규칙을 준 뒤 결과가 어떻게 달라지는지 비교한다

### 실습 아이디어

- 문서 요약
- 테스트 코드 생성
- 로그 정리
- 파일 정리

### 먼저 규칙 없이 요청

```text
output/summary.md에 docs/notes.md 요약을 저장해줘.
```

### 다음으로 규칙 파일을 만든 뒤 다시 요청

예시 규칙:

```markdown
# 작업 규칙

- 출력은 반드시 output/에 저장한다.
- 바로 완료하지 말고 검증 항목 3개를 먼저 적는다.
- 불확실한 내용은 추측하지 말고 확인 필요라고 표시한다.
- 실행 후 logs/에 실행 내용을 남긴다.
```

다시 요청:

```text
위 규칙을 따르면서 docs/notes.md를 요약해줘.
반드시 output/summary.md에 저장하고, 검증 항목도 함께 적어줘.
```

### 비교 포인트

- 출력 형식이 더 일관적인가
- 빠지는 항목이 줄었는가
- 검증 기준이 더 명확해졌는가
- 더 안전하게 행동하는가

### 입문자 기준 핵심

이 실습의 목적은 "규칙을 쓰면 완벽해진다"가 아니다.
핵심은 **규칙이 있으면 결과를 검토하기 쉬워진다**는 점을 체감하는 것이다.

---

## 3.8 실습 3: 최소 MCP 서버 직접 만들기

### 실습 목표

- 아주 작은 MCP 서버를 직접 만들고 테스트한다

### 추천 주제

- 현재 시각 반환
- 지정 폴더 파일 목록 반환
- 간단한 계산
- 로컬 메모 읽기

### 설계 원칙

- 도구 이름이 분명해야 한다
- 설명이 구체적이어야 한다
- 입력이 단순해야 한다
- 오류 메시지가 읽기 쉬워야 한다
- 가능하면 읽기 전용으로 시작한다

### Copilot 요청 예시

```text
Python으로 최소 MCP 서버 예제를 만들어줘.
요구사항:
- 읽기 전용 도구 1개만 제공
- 입력 검증이 있어야 함
- 오류 메시지가 명확해야 함
- 테스트 방법을 docs/server-design.md에 적어줘
```

### 학생이 직접 확인할 것

- 도구 설명이 충분히 구체적인가
- 잘못된 입력을 막는가
- 오류 메시지가 이해하기 쉬운가
- 테스트 절차가 실제로 가능한가

이 실습의 목표는 "대단한 서버"가 아니라 **MCP 구조를 눈으로 확인하는 것**이다.

---

## 3.9 실습 4: Plugin은 선택 실습으로 보기

### 왜 선택 실습인가

Plugin/App/Connector는 중요하지만, 입문 단계에서 가장 먼저 필요한 것은 아니다.

이번 주차의 우선순위는 아래 순서가 더 좋다.

1. MCP 연결
2. 규칙 파일 비교
3. 최소 MCP 서버 구현
4. 여유가 있으면 plugin 실습

### plugin을 한 줄로 이해하면

- 여러 skill, MCP 설정, 에이전트 설정을 한 번에 묶어 배포하는 단위

예시 구조:

```text
my-plugin/
  plugin.json
  skills/
    doc-summary/
      SKILL.md
  .mcp.json
```

입문자는 "plugin은 묶음 배포 방식" 정도만 이해해도 충분하다.

---

## 3.10 제출물

- MCP 사용 기록 1회 이상
- 규칙 적용 전후 비교 기록 1회
- 최소 MCP 서버 코드
- 실행 로그 1개 이상
- 출력 파일 1개 이상
- 체크리스트 또는 짧은 회고 문서

---

## 3.11 작업 전/후 체크리스트

### 작업 전

- 어떤 MCP를 연결할지 정했는가
- 어떤 작업으로 테스트할지 정했는가
- 출력 파일 위치를 정했는가
- 검증 방법을 정했는가
- 위험한 동작이 없는가

### 작업 후

- 실제로 MCP 호출이 일어났는가
- 결과 파일이 남았는가
- 로그가 남았는가
- 규칙 적용 전후 차이를 설명할 수 있는가
- 실패 사례가 있었다면 원인을 적었는가

---

## 3.12 핵심 정리

- **MCP는 도구 연결**이다
- **Skills / Instructions는 작업 규칙**이다
- **Plugin / App / Connector는 제품 안에서의 포장 방식**이다
- 실습에서는 "연결 성공"보다 **호출 기록과 검증**이 더 중요하다
- 최소 MCP 서버를 직접 만들어 보면 구조가 훨씬 빨리 이해된다

---

## 3.13 3주차에서 꼭 가져가야 할 것

3주차의 목표는 MCP와 Skills를 완벽하게 끝내는 것이 아니라, 둘의 차이를 이해하고 가장 기본적인 실습을 직접 해 보는 것이다.
따라서 이번 장에서는 아래 우선순위를 분명히 잡는 것이 중요하다.

### 지금 꼭 있어야 하는 것

- MCP와 Skills의 차이
- MCP 1회 연결 실습
- 규칙 파일 전후 비교 실습
- 최소 MCP 서버 1회 구현

### 있으면 좋지만 본문에서는 가볍게 다뤄도 되는 것

- plugin 상세 구조
- 제품별 메뉴 차이
- 여러 벤더의 확장 방식 비교
- 토큰 최적화, 대규모 운영 이슈

### 수업 운영 관점에서 추천

- 본문은 지금처럼 **핵심 개념 + 실습** 중심으로 짧게 유지
- 제품별 세부 차이와 확장 주제는 **부록 또는 참고 읽기**로 분리
- 학생이 실제로 해야 할 일은 각 실습마다 3~5단계로 더 단순하게 제시

즉, 3주차에서는 내용을 넓게 늘리기보다 **핵심 개념과 첫 실습 경험을 분명하게 만드는 것**이 더 중요하다.

---

## 부록 A. 다른 도구로 볼 때의 대응 관계

본문을 이해했다면 아래 표 정도만 잡아도 충분하다.

| 수업 개념 | GitHub Copilot | Codex / ChatGPT | Claude Code 계열 |
|----------|----------------|-----------------|------------------|
| 도구 연결 | MCP | MCP / Apps 뒤쪽 도구 계층 | MCP |
| 작업 규칙 | Instructions / Skills | Rules / Skills / `AGENTS.md` | Skills / 프로젝트 지침 |
| 묶음 배포 | Plugin | App 또는 패키지화된 구성 | Plugin |
| 자동 실행 | Hooks | Automations 등 | Hooks |
| 지속 문맥 | Memory | Memory | Memory |

핵심은 메뉴 이름을 외우는 것이 아니라, **역할을 번역해서 볼 수 있는가**이다.

---

## 참고 자료

- GitHub Copilot agent mode: https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-your-ide
- VS Code MCP 서버 설정: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- GitHub Agent Skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- GitHub custom instructions: https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
- OpenAI MCP docs: https://developers.openai.com/api/docs/mcp
- Codex Skills: https://developers.openai.com/codex/skills/
- Codex Rules: https://developers.openai.com/codex/rules/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude Code Skills: https://code.claude.com/docs/en/skills

---

## 다음 주 예고

- 4주차에서는 MCP 서버를 더 실전적으로 다룬다
- 인증, 실패 처리, 로깅, 테스트 가능한 구조를 갖춘 서버 설계로 확장한다
- 단순 연결을 넘어 실제 운영 가능한 도구 계층을 만드는 방향으로 발전시킨다
