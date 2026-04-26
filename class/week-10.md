# Week 10. LangGraph 멀티에이전트 실습 1: Supervisor와 핸드오프

> 학부 운영안 — 강의 + 3-에이전트 실습
> 참조: LangGraph 1.0 (2025-10 GA), `langgraph-supervisor` 패턴, LangSmith 트레이싱

---

## 학습 목표

- LangGraph **Supervisor 패턴**을 LLM + Pydantic **구조화 출력**(`with_structured_output`)으로 구현한다
- `Command`로 핸드오프를 만들고, 라우팅 흐름을 추적한다
- **Subgraph**로 한 에이전트 안에 또 작은 그래프를 둔다 (분석가 = 자체 검증 포함)
- **Send API**로 같은 에이전트를 여러 입력에 병렬로 돌린다
- **Checkpointer**로 대화의 중간 상태를 저장하고 이어서 실행한다
- LangSmith에서 멀티에이전트 트레이스(병렬 막대 포함)를 본다

---

## 이번 주 운영 원칙

- 9주차의 “핸드오프”를 **동적 라우팅**으로 확장한다
- 코드는 작게, 실행 결과는 항상 LangSmith로 본다
- “Supervisor가 매번 같은 순서를 도는 코드”는 멀티에이전트가 아니다 — *동적 결정*이 핵심

---

## 10.1 Supervisor 패턴이란

9주차의 순차형(`연구자 → 작성자`)은 흐름이 정해져 있다. **Supervisor 패턴**은 흐름을 *런타임에 결정*한다.

```text
        [Supervisor]  ← 매 턴마다 "다음에 누가 일할지" 결정
         /     |     \
   [연구자] [분석가] [작성자]
         \     |     /
          ──→ END
```

- Supervisor도 LLM이다
- 현재 상태를 보고 “다음 노드 이름”을 출력한다
- 모든 에이전트가 일을 끝내면 `END`로 보낸다

### 왜 동적 라우팅인가

- 작업이 단순하면 연구자만 부르고 끝낼 수 있다
- 사실 확인이 더 필요하면 연구자를 한 번 더 부른다
- 분석가가 데이터가 부족하다고 하면 다시 연구자에게 돌린다

순차형 그래프로는 표현하기 어려운 흐름이다.

---

## 10.2 핵심 개념 4가지

### (1) Command — 핸드오프 객체

LangGraph 1.0의 표준 핸드오프 방식이다.

```python
from langgraph.types import Command

def supervisor(state):
    # ... LLM이 "researcher" / "analyst" / "writer" / "FINISH" 중 하나를 출력
    next_agent = decide(state)
    if next_agent == "FINISH":
        return Command(goto="__end__")
    return Command(goto=next_agent)
```

`goto`는 다음에 실행할 노드 이름이다. `update`로 상태도 같이 바꿀 수 있다.

### (2) Subgraph — 그래프 안의 그래프

한 에이전트가 내부적으로 “생각 → 도구 호출 → 검토”의 작은 흐름을 갖는다고 하자. 별도 그래프로 만들어 큰 그래프에 *노드처럼* 끼운다.

```python
sub_builder = StateGraph(SubState)
sub_builder.add_node("draft", draft_node)
sub_builder.add_node("review", review_node)
sub_builder.add_edge(START, "draft")
sub_builder.add_edge("draft", "review")
sub_builder.add_edge("review", END)
sub_graph = sub_builder.compile()

main_builder.add_node("analyst", sub_graph)  # 그래프를 노드로 등록
```

이번 주 Step 8에서 *직접* 만든다.

### (3) Send API — 같은 노드를 여러 입력에 병렬로

같은 에이전트에게 N개 입력을 동시에 던지고 싶을 때 쓴다.

```python
from langgraph.types import Send

def fan_out(state):
    return [Send("summarize", {"doc": d}) for d in state["documents"]]
```

병렬 실행이 끝나면 결과가 자동으로 합쳐진다. Step 9에서 작은 예제를 직접 돌려 본다.

### (4) Checkpointer — 대화의 메모리

같은 사용자가 다음 턴에 “아까 그거 더 자세히”라고 하면, 이전 상태를 불러와야 한다. Checkpointer는 그래프의 모든 노드 결과를 저장한다.

```python
from langgraph.checkpoint.memory import InMemorySaver

graph = builder.compile(checkpointer=InMemorySaver())

# 같은 thread_id로 두 번 호출하면 메모리가 이어진다
config = {"configurable": {"thread_id": "user-42"}}
graph.invoke({"question": "..."}, config=config)
graph.invoke({"question": "더 자세히"}, config=config)
```

운영 환경에서는 `SqliteSaver`나 `PostgresSaver`를 쓰지만, 실습은 메모리 기반으로 충분하다.

---

## 10.3 만드는 것

> 사용자 질문을 받아 **연구자 → 분석가 → 작성자**가 협업해 답변을 만든다.
> Supervisor가 매번 누구에게 일을 줄지 결정한다.
> 같은 `thread_id`로 두 번째 질문을 하면 이전 대화를 기억한다.

```text
[질문 입력]
     ↓
[Supervisor]  ────┐
   │              │
   ▼              ▼
[연구자]       [분석가]
   │              │
   └──── [작성자] ─→ [최종 답변]
```

---

## 10.4 실행 환경

```bash
source .venv/bin/activate
cd practice/chapter10/code

pip install langgraph langchain-groq python-dotenv langsmith
```

`.env`에 다음을 둔다.

```bash
GROQ_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=week10-supervisor
```

LangSmith API 키가 없으면 트레이싱은 끄고 진행해도 된다 (아래 코드에 영향 없음).

---

## 10.5 제작 순서

### Step 1. 상태 정의

> **Copilot 프롬프트**
> ```
> supervisor.py 파일을 시작해줘.
> TypedDict로 TeamState를 정의한다.
> 필드:
>   - messages: 대화 기록(list)
>   - question: 사용자 질문(str)
>   - research: 연구자가 모은 사실(str)
>   - analysis: 분석가의 해석(str)
>   - draft: 작성자의 초안(str)
>   - next: 다음에 실행할 노드 이름(str)
> 각 필드에 한 줄 주석.
> ```

```python
# supervisor.py
from typing import TypedDict, Annotated
from operator import add
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")

class TeamState(TypedDict):
    messages: Annotated[list, add]  # 누적되는 대화 기록
    question: str                    # 사용자 질문
    research: str                    # 연구자 산출물
    analysis: str                    # 분석가 산출물
    draft: str                       # 작성자 초안
    next: str                        # Supervisor가 정한 다음 노드
```

`Annotated[list, add]`는 “여러 노드가 messages에 추가하면 합치라”는 뜻이다.

### Step 2. 세 명의 에이전트

> **Copilot 프롬프트**
> ```
> researcher, analyst, writer 함수를 작성해줘.
> 모두 TeamState를 받고 dict를 돌려준다.
>
> researcher: question을 보고 사실 5개를 정리한다.
> analyst: research를 받아 의미·시사점을 3줄로 분석한다.
>          데이터가 부족하면 첫 줄에 "RESEARCH_NEEDED"라고 적는다.
> writer: question + research + analysis를 보고 최종 답변을 만든다.
>
> 각 함수는 끝에 messages에 자신의 결과를 한 줄 요약해 추가한다.
> ```

```python
def researcher(state: TeamState) -> dict:
    prompt = (
        "다음 질문을 풀기 위해 필요한 사실을 5개 항목으로 정리하라. "
        "의견·평가는 쓰지 말고, 모르는 것은 '확인 필요'라고 적어라.\n\n"
        f"질문: {state['question']}"
    )
    research = llm.invoke(prompt).content
    return {
        "research": research,
        "messages": [f"[연구자] 사실 {research.count(chr(10)) + 1}개 정리 완료"],
    }

def analyst(state: TeamState) -> dict:
    prompt = (
        "다음 사실 정리를 보고 의미와 시사점을 3줄로 분석하라. "
        "사실이 부족해 분석이 어려우면 첫 줄에 정확히 'RESEARCH_NEEDED'만 출력하라.\n\n"
        f"사실 정리:\n{state['research']}"
    )
    analysis = llm.invoke(prompt).content
    return {
        "analysis": analysis,
        "messages": [f"[분석가] {'재조사 요청' if 'RESEARCH_NEEDED' in analysis else '분석 완료'}"],
    }

def writer(state: TeamState) -> dict:
    prompt = (
        "아래 자료를 근거로 학부생용 한국어 답변을 만들어라. "
        "자료에 없는 내용을 만들지 마라.\n\n"
        f"질문: {state['question']}\n\n"
        f"사실:\n{state['research']}\n\n"
        f"분석:\n{state['analysis']}"
    )
    draft = llm.invoke(prompt).content
    return {
        "draft": draft,
        "messages": ["[작성자] 초안 작성 완료"],
    }
```

### Step 3. Supervisor — LLM이 구조화 출력으로 결정한다

Supervisor는 *LLM*이다. 매 턴마다 “다음 노드 이름”을 골라 준다. 단어가 빗나가지 않게 **Pydantic 구조화 출력**(`with_structured_output`)을 쓴다 — 이게 LangChain·OpenAI·Anthropic의 표준 패턴이다.

> **Copilot 프롬프트**
> ```
> Pydantic으로 Route 모델을 만든다. next: Literal["researcher","analyst","writer","FINISH"].
> ChatGroq에 .with_structured_output(Route)를 붙인 supervisor를 작성한다.
> 시스템 프롬프트에 4개 분기 규칙(research 비면 researcher, RESEARCH_NEEDED면 researcher,
> analysis 비면 analyst, draft 비면 writer, draft 있으면 FINISH)을 자연어로 적어 준다.
> 결과의 next에 따라 Command(goto=...)로 보낸다.
> ```

```python
from typing import Literal
from pydantic import BaseModel, Field

class Route(BaseModel):
    """Supervisor가 다음에 호출할 에이전트."""
    next: Literal["researcher", "analyst", "writer", "FINISH"] = Field(
        description="다음 단계로 보낼 에이전트 이름. 모두 끝났으면 FINISH."
    )

router_llm = llm.with_structured_output(Route)

SUPERVISOR_SYSTEM = """\
너는 멀티에이전트 팀의 supervisor다. 현재 상태를 보고 다음에 일할 사람을 고른다.

규칙:
- research가 비어 있으면 researcher
- analysis 안에 RESEARCH_NEEDED가 있으면 researcher (다시 조사)
- research가 있고 analysis가 비어 있으면 analyst
- analysis가 있고 draft가 비어 있으면 writer
- draft가 채워져 있으면 FINISH
"""

def supervisor(state: TeamState) -> Command:
    summary = (
        f"research_len={len(state.get('research') or '')} "
        f"analysis={(state.get('analysis') or '')[:80]!r} "
        f"draft_len={len(state.get('draft') or '')}"
    )
    route: Route = router_llm.invoke(SUPERVISOR_SYSTEM + "\n\n상태: " + summary)
    print(f"[Supervisor] → {route.next}")
    if route.next == "FINISH":
        return Command(goto=END, update={"next": "FINISH"})
    return Command(goto=route.next, update={"next": route.next})
```

핵심 두 가지:
1. **LLM이 결정**한다 — `if-else`가 아니다. RESEARCH_NEEDED 같은 *언어적 단서*도 자연스럽게 처리한다.
2. **구조화 출력**이 “이상한 텍스트”를 막는다 — `next`가 반드시 4개 중 하나가 된다. 파싱 실패 없음.

이게 production 멀티에이전트의 표준 라우팅 방식이다.

### Step 4. 그래프 조립

> **Copilot 프롬프트**
> ```
> StateGraph로 supervisor + researcher + analyst + writer를 연결한다.
> START → supervisor.
> 각 작업자 노드는 작업이 끝나면 다시 supervisor로 돌아간다.
> InMemorySaver를 checkpointer로 쓴다.
> 컴파일된 graph를 만든다.
> ```

```python
builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher)
builder.add_node("analyst", analyst)
builder.add_node("writer", writer)

builder.add_edge(START, "supervisor")
# 각 작업자는 끝나면 supervisor로 복귀
builder.add_edge("researcher", "supervisor")
builder.add_edge("analyst", "supervisor")
builder.add_edge("writer", "supervisor")

graph = builder.compile(checkpointer=InMemorySaver())
```

흐름:
```
START → supervisor → (researcher | analyst | writer) → supervisor → ... → END
```

Supervisor가 매번 호출되면서 다음 노드를 정한다.

### Step 5. 실행 + 두 번째 질문 이어서

> **Copilot 프롬프트**
> ```
> 같은 thread_id로 두 번 호출하는 main을 작성해줘.
> 1) 처음: "2025년 LangGraph 1.0의 변경점 3가지 정리해줘"
> 2) 두 번째: "그중 가장 학부생에게 중요한 한 가지를 골라 더 풀어줘"
> 두 번째 호출에서 이전 research/analysis가 그대로 남아 있는지 확인한다.
> ```

```python
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo-1"}}

    # 1차 질문
    state1 = graph.invoke(
        {
            "messages": [],
            "question": "2025년 LangGraph 1.0의 변경점 3가지를 학부생에게 설명해줘.",
            "research": "", "analysis": "", "draft": "", "next": "",
        },
        config=config,
    )
    print("\n=== 1차 답변 ===")
    print(state1["draft"])

    # 2차 질문 — 이전 컨텍스트가 살아 있어야 함
    state2 = graph.invoke(
        {
            "messages": [],
            "question": "그중 학부생에게 가장 중요한 한 가지만 골라 더 풀어줘.",
            "research": state1["research"],     # 명시적으로 이어 줌
            "analysis": state1["analysis"],
            "draft": "",
            "next": "",
        },
        config=config,
    )
    print("\n=== 2차 답변 ===")
    print(state2["draft"])

    print("\n=== 누적 메시지 ===")
    for m in state2["messages"]:
        print("-", m)
```

### Step 6. LangSmith로 트레이스 보기

`.env`에 LangSmith 키가 있고 `LANGSMITH_TRACING=true`라면, https://smith.langchain.com 에서 자동으로 트레이스가 보인다.

확인할 것:
- `supervisor` 노드가 몇 번 호출됐는가
- `researcher`로 *두 번 이상* 돌아간 사례가 있는가 (RESEARCH_NEEDED 분기)
- 각 노드의 입력 토큰, 출력 토큰, 응답 시간

### Step 7. 의도적으로 RESEARCH_NEEDED 만들기

> **Copilot 프롬프트**
> ```
> 모르는 주제로 질문해서 분석가가 RESEARCH_NEEDED를 출력하게 만든다.
> 예: "2099년 한국의 우주 정책 핵심 3가지"
> Supervisor가 다시 researcher로 돌리는지 확인한다.
> ```

이때 무한 루프가 나면 **재시도 횟수 제한**이 필요함을 학생이 직접 체감한다 (다음 단계 과제).

```python
# 안전장치: 최대 6번 supervisor 호출 후 강제 종료
graph = builder.compile(
    checkpointer=InMemorySaver(),
)
graph.invoke(initial_state, config={
    **config,
    "recursion_limit": 12,  # supervisor + 작업자 합쳐 12 단계까지만
})
```

`recursion_limit`은 LangGraph가 무한 루프를 막는 안전장치다. 학부 실습에서는 8~12 정도로 둔다.

### Step 8. Subgraph — 분석가를 작은 그래프로 교체

분석가가 “초안 분석 → 자체 검증”의 두 단계로 일하게 만든다.

> **Copilot 프롬프트**
> ```
> AnalystState TypedDict (research, analysis, self_check) 만든다.
> draft_analysis 노드: research 보고 analysis 작성.
> self_check 노드: analysis가 사실에 근거하는지 LLM이 검토, 문제 있으면 analysis 끝에 "(자체검증: 보완 필요)" 추가.
> StateGraph로 START -> draft_analysis -> self_check -> END 연결.
> compile()한 sub_graph를 main builder에 add_node("analyst", sub_graph)로 등록.
> ```

```python
class AnalystState(TypedDict):
    research: str
    analysis: str

def draft_analysis(state: AnalystState) -> dict:
    prompt = f"다음 사실을 보고 의미·시사점을 3줄로 분석:\n{state['research']}"
    return {"analysis": llm.invoke(prompt).content}

def self_check(state: AnalystState) -> dict:
    prompt = (
        f"아래 분석이 사실 정리에 근거 있는지 'OK' 또는 '보완 필요'로 한 단어로 답.\n"
        f"사실: {state['research']}\n분석: {state['analysis']}"
    )
    verdict = llm.invoke(prompt).content.strip()
    suffix = "" if "OK" in verdict.upper() else " (자체검증: 보완 필요)"
    return {"analysis": state["analysis"] + suffix}

sub = StateGraph(AnalystState)
sub.add_node("draft", draft_analysis)
sub.add_node("check", self_check)
sub.add_edge(START, "draft")
sub.add_edge("draft", "check")
sub.add_edge("check", END)
analyst_subgraph = sub.compile()

# 기존 add_node("analyst", analyst)를 아래로 교체
builder.add_node("analyst", analyst_subgraph)
```

같은 인터페이스(`research → analysis`)이므로 Supervisor 코드는 손대지 않아도 된다. **Subgraph가 노드처럼 끼워진다**는 핵심을 본다.

### Step 9. Send API — 연구자를 병렬로

같은 질문에 대해 연구자가 “기술 측면 / 사용자 측면 / 한계 측면” 세 관점을 *병렬로* 정리한다.

> **Copilot 프롬프트**
> ```
> ParallelState TypedDict: question, perspectives(list[str]), parts(Annotated[list[str], add])
> distribute 노드: state["perspectives"]에 ["기술", "사용자", "한계"] 채워 넣고,
> Send를 써서 각 관점마다 perspective_research 노드를 호출.
> perspective_research 노드: question + perspective로 짧은 정리 1개 만들고 parts에 추가.
> merge 노드: parts를 하나의 research로 합쳐서 state.research에 저장.
> 작은 별도 그래프(parallel_graph)로 컴파일.
> ```

```python
from typing import Annotated
from langgraph.types import Send

class ParallelState(TypedDict):
    question: str
    perspectives: list[str]
    parts: Annotated[list[str], add]
    research: str

def distribute(state: ParallelState):
    return [
        Send("perspective_research", {"question": state["question"], "perspective": p})
        for p in ["기술", "사용자", "한계"]
    ]

def perspective_research(state: dict) -> dict:
    prompt = f"{state['question']}을(를) '{state['perspective']}' 관점에서 3줄로 정리."
    return {"parts": [f"[{state['perspective']}] " + llm.invoke(prompt).content]}

def merge(state: ParallelState) -> dict:
    return {"research": "\n\n".join(state["parts"])}

p = StateGraph(ParallelState)
p.add_node("perspective_research", perspective_research)
p.add_node("merge", merge)
p.add_conditional_edges(START, distribute, ["perspective_research"])
p.add_edge("perspective_research", "merge")
p.add_edge("merge", END)
parallel_research = p.compile()

# 단독 실행으로 결과 확인
out = parallel_research.invoke({"question": "LangGraph 1.0", "perspectives": [], "parts": [], "research": ""})
print(out["research"])
```

3번의 LLM 호출이 *동시*에 나간다. LangSmith 트레이스에서 병렬 막대를 본다.

---

## 10.6 라우팅 로그 만들기

`messages` 필드에 누적된 “누가 무엇을 했는지”가 자동으로 라우팅 로그가 된다. 다음처럼 출력해 본다.

```python
print("\n=== 라우팅 로그 ===")
for i, m in enumerate(state2["messages"], 1):
    print(f"{i:>2}. {m}")
```

예상 출력:
```
=== 라우팅 로그 ===
 1. [연구자] 사실 5개 정리 완료
 2. [분석가] 분석 완료
 3. [작성자] 초안 작성 완료
 4. [연구자] 사실 4개 정리 완료
 5. [분석가] 분석 완료
 6. [작성자] 초안 작성 완료
```

---

## 10.7 자주 만나는 실수와 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 무한 루프 | Supervisor가 매번 같은 노드를 부른다 | `recursion_limit` + Supervisor 규칙에 “최대 1회 재시도” 추가 |
| draft가 텅 빈다 | Supervisor가 writer를 못 부른다 | 상태 요약 문자열에 draft 길이를 0으로만 보여줘서 결정 못함 — 더 명확한 단서 추가 |
| 첫 결과가 엉성하다 | 연구자가 모르는 주제 | “모르면 확인 필요라고 적어라” 지시 강화 |
| LangSmith 트레이스가 안 보인다 | 환경변수 미적용 | `.env` 다시 로드, `LANGSMITH_TRACING=true` 확인 |
| messages가 누적되지 않는다 | TypedDict에 `Annotated[list, add]` 누락 | 리듀서 추가 |

---

## 10.8 제출물

### 필수 (90분 안에 끝낼 수 있는 양)

- `supervisor.py` 전체 코드 (Step 1~9 모두 포함)
- 구조화 출력 Supervisor 동작 확인 — 정상 질문 1회 + 모르는 주제 1회
- Subgraph 분석가가 “자체검증: 보완 필요” 표기를 단 사례 1개
- Send API 병렬 연구 결과 + LangSmith 병렬 트레이스 캡처
- 라우팅 로그 출력
- 5문장 회고

### 회고 질문

1. Supervisor가 작업자에게 일을 잘못 보낸 사례가 있었는가
2. RESEARCH_NEEDED 분기가 실제로 작동했는가
3. 두 번째 질문이 이전 research를 어떻게 활용했는가
4. 9주차의 단순 핸드오프와 비교해 무엇이 좋아졌는가
5. 11주차의 코딩 에이전트 실습에서 비슷한 분기 결정을 어떻게 만들 수 있겠는가

---

## 체크리스트

- Pydantic `with_structured_output`으로 Supervisor를 만들었다
- Supervisor가 매 턴 다음 노드를 *동적으로* 결정한다
- `Command(goto=...)`로 핸드오프를 구현했다
- `Annotated[list, add]` 리듀서로 messages가 누적된다
- Checkpointer로 같은 thread_id의 두 번째 호출이 이어진다
- 분석가를 **Subgraph**로 교체해 자체 검증을 추가했다
- **Send API**로 연구자를 병렬로 돌렸고 LangSmith에서 병렬 막대를 봤다
- `recursion_limit`로 무한 루프를 막을 수 있다는 것을 안다

---

## 참고 자료

- LangGraph Multi-Agent: https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- LangGraph Supervisor 튜토리얼: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/
- LangGraph Send API: https://langchain-ai.github.io/langgraph/concepts/low_level/#send
- LangGraph Checkpointer: https://langchain-ai.github.io/langgraph/concepts/persistence/
- LangSmith Tracing: https://docs.smith.langchain.com/observability

---

## 다음 주 예고

11주차에는 시각을 바꾼다. 직접 LangGraph로 멀티에이전트를 짜는 대신, 학생이 가진 **코딩 에이전트(GitHub Copilot · Antigravity · Claude Code 중 하나)**에 작업을 위임하고 *계획 검토·결과 검토*의 두 게이트를 거치는 공통 6단계 워크플로를 배운다. 멀티에이전트의 본질이 “여러 모델을 부른다”가 아니라 “책임을 분리하고 검증한다”에 있음을 도구를 바꾸어 다시 확인한다.
