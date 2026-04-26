# Week 9. 멀티에이전트 개념: 단일 vs 멀티, 4대 패턴, 평가

> 학부 운영안 — 강의 + 작은 코드 비교
> 참조: Notion ch6 「멀티 에이전트 시스템」, Anthropic 「How we built our multi-agent research system」(2025), Cognition 「Don't build multi-agents」(2025)

---

## 학습 목표

- 단일 에이전트의 한계를 자신의 코드에서 직접 확인한다
- 멀티에이전트의 4대 패턴(계층형·협력형·순차형·시장형)을 구분한다
- 핸드오프와 공유 메모리의 역할을 설명한다
- 멀티에이전트가 “필요한 작업”과 “쓰지 말아야 할 작업”을 자신의 사례로 판단한다
- LangGraph로 2-에이전트 핸드오프를 직접 구현한다

---

## 이번 주 운영 원칙

- 프레임워크 비교에 시간을 쓰지 않는다 — LangGraph 한 가지로만 실습한다
- “멀티에이전트가 멋있어서” 쓰는 것이 아니라 “단일 에이전트로는 풀리지 않아서” 쓰는 감각을 만든다
- 같은 작업을 단일/멀티 두 방식으로 만들어 직접 비교한다

---

## 9.1 왜 멀티에이전트인가

하나의 에이전트가 모든 일을 맡으면 다음 문제가 생긴다.

| 문제 | 어떻게 드러나는가 |
|---|---|
| 컨텍스트 비대 | 한 대화에 계획·구현·테스트·문서가 모두 섞인다. 모델이 중요한 제약을 놓친다 |
| 역할 혼재 | 검토자처럼 굴어야 할 순간에 작성자처럼 답한다 |
| 검증 약화 | 자기 산출물을 자기가 검토하므로 같은 실수를 반복한다 |
| 추적 불가 | 어디서 잘못됐는지 대화 흐름에서만 확인할 수 있다 |

**멀티에이전트의 기본 아이디어**: 일을 책임 단위로 쪼개고, 각 에이전트가 자기 책임만 맡게 한다.

```text
[사용자 질문]
     │
     ▼
[연구자]  ── 정보 모은다
     │
     ▼
[작성자]  ── 답변을 만든다
     │
     ▼
[검토자]  ── 사실·논리·범위를 점검한다
     │
     ▼
[최종 답변]
```

다만 역할을 나누면 **조정 비용**이 든다. 작은 함수 하나 고치는 일에는 멀티에이전트가 오히려 느리고 번거롭다.

---

## 9.2 멀티에이전트, 좋은가 나쁜가 (2025년 두 입장)

| 입장 | 누가 | 핵심 한 줄 |
|---|---|---|
| 찬성 | Anthropic | 일을 *나눠서* 시키니 단일 에이전트보다 훨씬 잘하더라 |
| 신중 | Cognition (Devin) | *섣불리* 나누면 에이전트끼리 가정이 안 맞아 더 헤맨다 |

**대립이 아니라 조건의 차이**다.

| 잘 작동하는 작업 | 망하는 작업 |
|---|---|
| 하위 작업이 분명히 나뉜다 | 한 흐름의 결정이다 |
| 각 단계의 입출력이 또렷하다 | 단계 간 가정이 암묵적이다 |
| 병렬로 시간을 줄일 수 있다 | 직렬에서 검증만 더하면 충분하다 |

판단 기준 한 줄: **작업을 2개 이상의 독립된 입출력으로 설명할 수 있는가.**

---

## 9.3 단일 에이전트와 멀티에이전트 비교

| 항목 | 단일 에이전트 | 멀티에이전트 |
|---|---|---|
| 구조 | 단순 | 복잡 |
| 구현 비용 | 낮음 | 높음 |
| 역할 분리 | 약함 | 강함 |
| 검증 루프 | 사용자가 챙겨야 함 | 검토 역할을 별도로 둘 수 있음 |
| 추적 가능성 | 대화 흐름에 의존 | 핸드오프·로그·트레이스로 남음 |
| 적합한 작업 | 작은 수정, 단순 자동화 | 조사 + 작성 + 검토, 데이터 + 분석 + 보고 |

---

## 9.4 4대 패턴

학부 수업에서는 다음 네 가지만 다룬다. 실제 프로젝트의 90%는 이 안에서 해결된다.

### 패턴 1. 순차형 (Sequential)

가장 단순하다. 한 에이전트의 출력이 다음 에이전트의 입력이 된다.

```text
[연구자] ─→ [작성자] ─→ [검토자]
```

- 장점: 흐름이 명확하다, 디버깅이 쉽다
- 단점: 병렬 처리가 안 된다
- 학부 실습에서 가장 안전한 출발점

### 패턴 2. 계층형 (Hierarchical / Supervisor)

관리자(Supervisor) 에이전트가 작업 전체를 보고, 하위 에이전트에게 작업을 나눠 준다.

```text
        [Supervisor]
         /     |     \
   [연구자] [작성자] [검토자]
```

- 장점: 작업 분배가 동적이다, 실패 시 다시 다른 에이전트로 돌릴 수 있다
- 단점: Supervisor 설계가 잘못되면 무한 루프
- LangGraph의 표준 패턴 (10주차 실습)

### 패턴 3. 협력형 (Cooperative / Parallel)

여러 에이전트가 같은 목표를 향해 병렬로 일한다.

```text
[연구자A] ┐
[연구자B] ├─→ [통합자]
[연구자C] ┘
```

- 장점: 빠르다, Anthropic 사례에서 강한 패턴
- 단점: 결과 충돌·중복 처리 필요

### 패턴 4. 시장형 (Market / Auction)

여러 에이전트가 입찰처럼 작업을 가져간다. 학부 수업에서는 *개념만* 다룬다.

- 사용 예: 도구가 많고, 어떤 도구가 잘할지 미리 모를 때
- 단점: 구현 복잡도가 매우 높음

---

## 9.5 핸드오프와 공유 메모리

### 핸드오프(Handoff)

한 에이전트가 “이건 내 일이 아니다, 다음 에이전트가 처리해라”라고 넘기는 행위다.

LangGraph에서는 `Command` 객체로 표현한다.

```python
from langgraph.types import Command

def researcher(state):
    # ... 조사 작업
    return Command(
        goto="writer",                   # 다음 에이전트로 넘김
        update={"research_notes": notes} # 상태에 결과 추가
    )
```

핵심은 **다음 에이전트가 받을 수 있는 형태로 결과를 정리**해 두는 것이다.

### 공유 메모리

에이전트들이 같이 보는 상태(State)다. LangGraph에서는 `TypedDict`로 정의한다.

```python
from typing import TypedDict

class TeamState(TypedDict):
    question: str         # 사용자 질문
    research_notes: str   # 연구자 산출물
    draft: str            # 작성자 산출물
    review: str           # 검토자 산출물
    final: str            # 최종 답변
```

학부생이 자주 하는 실수: **모든 에이전트가 모든 필드를 다 본다**고 생각한다. 실제로는 *각 에이전트가 자신에게 필요한 필드만 읽어야* 컨텍스트가 깨끗해진다.

---

## 9.6 멀티에이전트 평가: 무엇을 보는가

세 벤치마크는 *이름만* 알아 둔다.

| 벤치마크 | 한 줄 |
|---|---|
| **GAIA** | 도구를 조합해야 풀리는 일반 질문 |
| **AgentBench** | 웹·DB·OS 등 8개 환경에서 다단계 추론 |
| **WebArena** | 실제 웹 사이트에서 작업 완료율 |

수업에서는 더 단순한 4가지를 본다.

1. 작업 완료율 — 의도한 산출물이 나왔는가
2. 근거 — 왜 그렇게 답했는지 설명할 수 있는가
3. 실패 인지 — 모르는 것을 “모른다”고 답하는가
4. 사람 개입 횟수 — 끝까지 가기 위해 몇 번 손댔는가

---

## 9.7 언제 멀티에이전트를 쓰지 말아야 하는가

**이번 주에서 가장 중요한 부분**이다. 다음에 해당하면 단일 에이전트가 낫다.

- 작업이 5분 안에 끝나는 작은 수정이다
- 변경 파일이 1개이고 테스트도 단순하다
- 역할을 나누어도 입출력이 분명해지지 않는다
- 한 에이전트의 답을 다른 에이전트가 그대로 옮겨 쓰게 된다 (역할이 같다는 신호)
- 도구 권한을 통제하기 어렵다

“멀티에이전트로 만들었다”는 자체가 가치가 아니다. **단일 에이전트로 안 풀리는 이유**를 한 문장으로 말할 수 없다면, 단일 에이전트로 시작한다.

---

## 9.8 실습: 같은 작업을 단일/멀티 두 가지로 만들기

### 실습 시나리오

> 사용자가 “2025년 LangGraph 1.0의 변경점을 정리해줘”라고 묻는다.
> (1) 단일 에이전트 버전, (2) 2-에이전트 핸드오프 버전을 만든다.
> 같은 입력에 대해 결과·시간·실수를 비교한다.

이번 주는 검색 도구 없이 **모델의 추론**만으로 답하게 한다 (검색은 12주차에 추가).

### 실행 환경

```bash
# 프로젝트 루트에서
source .venv/bin/activate

cd practice/chapter9/code
pip install langgraph langchain-groq python-dotenv
```

`.env`에 `GROQ_API_KEY`가 있는지 확인한다.

### Step 1. 단일 에이전트 버전

> **Copilot 프롬프트**
> ```
> single_agent.py 파일을 만들어줘.
> ChatGroq(model="llama-3.3-70b-versatile")를 써서
> 사용자 질문 하나를 받아 답변을 생성하는 단순 함수 ask(question)을 만들어줘.
> .env를 load_dotenv로 불러오고, 답변과 응답 시간을 출력해줘.
> ```

```python
# single_agent.py
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")

def ask(question: str) -> str:
    start = time.time()
    result = llm.invoke(question)
    elapsed = time.time() - start
    print(f"[단일] {elapsed:.1f}s")
    return result.content

if __name__ == "__main__":
    answer = ask("2025년 LangGraph 1.0의 주요 변경점 3가지를 정리해줘.")
    print(answer)
```

이 버전은 **연구도 검토도 같은 모델 한 번**에 한다.

### Step 2. 멀티에이전트 버전 (연구자 → 작성자)

> **Copilot 프롬프트**
> ```
> multi_agent.py 파일을 만들어줘.
> LangGraph의 StateGraph로 두 에이전트를 연결한다.
>
> 상태 (TypedDict):
>   - question: 사용자 질문
>   - notes: 연구자가 만든 자료 정리
>   - answer: 작성자가 만든 최종 답변
>
> 노드:
>   - researcher: question을 받아 "사실 정리"만 한다. 의견·평가 금지.
>   - writer: question + notes를 받아 학부생용 한국어 요약을 만든다.
>
> 흐름: START -> researcher -> writer -> END
> ChatGroq(model="llama-3.3-70b-versatile") 사용.
> 각 노드 진입 시 print로 시간을 찍는다.
> ```

```python
# multi_agent.py
import time
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")

class TeamState(TypedDict):
    question: str
    notes: str
    answer: str

def researcher(state: TeamState) -> dict:
    t = time.time()
    prompt = (
        "다음 질문에 답하기 위해 필요한 사실을 5개 항목으로 정리해라. "
        "의견이나 평가는 쓰지 마라. 모르는 것은 '확인 필요'라고 적어라.\n\n"
        f"질문: {state['question']}"
    )
    notes = llm.invoke(prompt).content
    print(f"[연구자] {time.time() - t:.1f}s")
    return {"notes": notes}

def writer(state: TeamState) -> dict:
    t = time.time()
    prompt = (
        "아래 사실 정리를 근거로, 학부생이 이해할 수 있는 한국어 요약을 만들어라. "
        "사실 정리에 없는 내용을 만들지 마라.\n\n"
        f"질문: {state['question']}\n\n"
        f"사실 정리:\n{state['notes']}"
    )
    answer = llm.invoke(prompt).content
    print(f"[작성자] {time.time() - t:.1f}s")
    return {"answer": answer}

builder = StateGraph(TeamState)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_edge(START, "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({
        "question": "2025년 LangGraph 1.0의 주요 변경점 3가지를 정리해줘.",
        "notes": "",
        "answer": "",
    })
    print("\n--- 최종 답변 ---")
    print(result["answer"])
    print("\n--- 연구자 메모 (디버깅용) ---")
    print(result["notes"])
```

### Step 3. 두 결과 비교

같은 질문으로 두 파일을 각각 실행하고, 다음 표를 채운다.

| 항목 | 단일 에이전트 | 멀티에이전트 |
|---|---|---|
| 응답 시간 |  |  |
| 답변 길이 |  |  |
| 사실로 보이지만 의심스러운 문장 수 |  |  |
| “모른다”고 인정한 부분 |  |  |
| 인용/근거 표기 유무 |  |  |

### Step 4. 의도적으로 멀티에이전트가 *불리한* 경우 만들기

> **Copilot 프롬프트**
> ```
> 위 두 파일을 그대로 두고, 다음 단순 질문으로 한 번 더 실행한다.
> "1 + 1은?"
> 두 결과를 비교한다.
> ```

이때 멀티에이전트의 응답 시간이 단일보다 길다는 것을 직접 본다. **모든 작업에 멀티에이전트가 좋은 게 아니다**라는 감각을 만든다.

---

## 9.9 활동: 자기 도메인에 적용해 보기

### 목표

각자 관심 있는 도메인에서 “단일로 안 풀리는 작업”을 한 개 찾는다.

### 활동 방법

1. 자기 도메인을 한 줄로 정한다 (예: 학과 공지 요약, 논문 검색, 게임 가이드 작성).
2. 그 도메인에서 자주 하는 작업을 1개 고른다.
3. 그 작업을 단일 에이전트로 만들었을 때의 한계를 3줄 적는다.
4. 멀티에이전트로 만든다면 어떤 역할로 나눌지 적는다 (최소 2명).
5. 각 역할의 입력·출력·검증 기준을 적는다.

### 설계표

```markdown
## 멀티에이전트 설계표

- 도메인:
- 작업:
- 단일 에이전트로 부족한 이유 (3줄):
- 역할 1: 입력 / 작업 / 출력 / 검증 기준
- 역할 2: 입력 / 작업 / 출력 / 검증 기준
- 역할 3 (선택): 입력 / 작업 / 출력 / 검증 기준
- 사람 승인 지점:
- 멀티에이전트가 더 나아질 것이라 보는 근거:
```

이 설계표는 14주차 최종 프로젝트 주제의 출발점이 될 수 있다.

---

## 9.10 제출물

### 필수

- `single_agent.py`, `multi_agent.py` 코드
- 같은 질문에 대한 두 실행 결과 캡처
- “1 + 1은?” 같은 단순 질문에 대한 두 실행 결과 캡처
- 비교 표 (Step 3 표 채워서)
- 멀티에이전트 설계표 1개 (자기 도메인)
- 5문장 회고

### 회고 질문

1. 어떤 질문에서 멀티에이전트가 단일보다 분명히 나았는가
2. 어떤 질문에서 단일이 더 나았는가
3. 두 에이전트가 컨텍스트를 어떻게 나누고 있는가 (코드의 `state`)
4. 자기 도메인의 작업에서 역할을 어떻게 나누었는가
5. 다음 주(10주차)의 Supervisor 패턴을 적용한다면 무엇이 달라질 것인가

---

## 체크리스트

- 단일 에이전트의 한계 4가지를 자기 코드 위에서 설명할 수 있다
- 4대 패턴(순차·계층·협력·시장)을 한 줄씩 설명할 수 있다
- 핸드오프와 공유 메모리의 차이를 설명할 수 있다
- LangGraph로 2-에이전트 핸드오프를 직접 만들었다
- 멀티에이전트가 *불리한* 경우를 자기 코드로 보였다
- 자기 도메인의 작업으로 멀티에이전트 설계표를 만들었다

---

## 참고 자료

- Anthropic 「How we built our multi-agent research system」 (2025)
- Cognition 「Don't build multi-agents」 (2025)
- LangGraph 1.0 GA 발표: https://changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available
- LangGraph Multi-Agent 가이드: https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- GAIA 벤치마크: https://huggingface.co/gaia-benchmark
- Notion ch6 「멀티 에이전트 시스템」

---

## 다음 주 예고

10주차에는 LangGraph의 **Supervisor 패턴**으로 3-에이전트 시스템을 구현한다. Supervisor가 동적으로 어떤 에이전트에게 일을 줄지 결정하는 흐름과, 체크포인터로 대화를 이어 가는 방법을 다룬다.
