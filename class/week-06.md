# Week 6. LangGraph 기초: 상태·분기·반복

> 학부 운영안 기준 축약본
> 원본 심화 내용: `docs/ch6.md`

## 학습 목표

- LangGraph의 상태(State) 개념을 설명한다
- 조건 분기와 반복 루프를 구현한다
- 하나의 작은 예제를 처음부터 끝까지 완성한다

---

## 이번 주 운영 원칙

- 수업 중: 이론 1시간
- 수업 후: 개별 홈과제로 실습 진행
- 이론과 홈과제는 **동일한 예제** 하나를 중심으로 연결된다
- LangSmith, Store API, 외부 저장소는 필수 범위가 아니다

### 이번 주 예제: 한 줄 설명 생성기

> 주제어를 입력하면 LLM이 한 줄 설명을 생성하고, 다른 LLM이 품질을 판정한다.  
> 통과하면 출력하고 종료. 부족하면 다시 생성. 최대 3회.

이 예제 하나로 상태, 분기, 반복 세 가지 개념을 모두 다룬다.

### 필수 범위

- 상태 모델
- 조건 분기
- 반복 루프와 종료 조건

### 심화 읽기

- LangSmith
- 장기 메모리
- 외부 저장소 통합

---

## ─ 이론 (1시간) ─

---

## 6.1 왜 LangGraph가 필요한가

Week 5에서 만든 에이전트는 "도구를 한 번 고르고 호출한다"는 구조였다.  
그런데 현실에서는 결과를 보고 방향을 바꿔야 할 때가 많다.

예를 들어:

- 생성된 설명이 너무 짧으면 다시 생성해야 함
- 검증 결과가 나빠도 무조건 진행해서는 안 됨
- 시도가 몇 번인지 기억하면서 흐름을 제어해야 함

이런 상황에서는 단순한 함수 호출 순서가 아니라 **흐름을 통제하는 구조**가 필요하다.  
LangGraph는 그 구조를 제공한다.

핵심 장점 세 가지:

- 상태를 코드로 정의할 수 있음 — 지금 어디까지 왔는지 항상 알 수 있음
- 분기 조건을 코드로 통제할 수 있음 — LLM 판단이 아니라 개발자가 규칙을 씀
- 반복 종료 조건을 명확히 넣을 수 있음 — 무한 루프 없이 안전하게 반복함

---

## 6.2 상태(State) 모델

상태는 워크플로우 전체가 공유하는 데이터 묶음이다.  
노드는 상태를 읽고, 일부 필드를 갱신한 뒤 반환한다.

이번 주 예제의 상태:

```python
from typing import TypedDict

class ExplainerState(TypedDict):
    topic: str          # 입력: 설명할 주제
    explanation: str    # 현재 생성된 한 줄 설명
    is_ok: bool         # 검사 결과: 통과 여부
    attempt: int        # 시도 횟수
```

상태를 보면 이 워크플로우가 무엇을 하는지 바로 알 수 있다.  
이번 주에는 "현재 작업이 어디까지 왔는지"를 저장하는 용도로만 이해하면 충분하다.

---

## 6.3 노드

노드는 상태를 받아서 일부를 바꾸고 돌려주는 함수다.  
이번 예제에는 노드가 두 개 있다.

**generate 노드** — 설명 생성

```python
from langchain_groq import ChatGroq

llm = ChatGroq(model="llama-3.3-70b-versatile")

def generate(state: ExplainerState) -> dict:
    prompt = f"'{state['topic']}'을 비전공자에게 한 문장으로 설명해라."
    result = llm.invoke(prompt)
    return {
        "explanation": result.content,
        "attempt": state["attempt"] + 1,
    }
```

**check 노드** — 품질 판정

```python
def check(state: ExplainerState) -> dict:
    prompt = (
        f"다음 설명이 비전공자에게 명확한가? '{state['explanation']}'\n"
        "명확하면 'yes', 아니면 'no'만 답해라."
    )
    result = llm.invoke(prompt)
    return {"is_ok": result.content.strip().lower() == "yes"}
```

각 노드는 **변경할 필드만** 딕셔너리로 반환한다. 나머지 필드는 그대로 유지된다.

---

## 6.4 조건 분기

노드 실행 후 다음에 어디로 갈지 결정하는 함수다.

```python
def route(state: ExplainerState) -> str:
    if state["is_ok"]:
        return "end"
    if state["attempt"] >= 3:
        return "end"
    return "generate"
```

핵심 규칙 두 가지:

- 분기 조건은 사람이 읽을 수 있게 명시적으로 쓴다
- 반드시 종료 조건을 넣는다 — 없으면 무한 루프가 생긴다

---

## 6.5 그래프 조립

노드와 분기를 연결해서 그래프를 만든다.

```python
from langgraph.graph import StateGraph, END

builder = StateGraph(ExplainerState)

builder.add_node("generate", generate)
builder.add_node("check", check)

builder.set_entry_point("generate")
builder.add_edge("generate", "check")
builder.add_conditional_edges("check", route, {"end": END, "generate": "generate"})

graph = builder.compile()
```

흐름 요약:

```
[START] → generate → check → (통과 또는 3회 초과) → [END]
                       ↑              |
                       └── 재생성 ────┘
```

---

## ─ 홈과제 ─

---

## 6.6 홈과제: 한 줄 설명 생성기 직접 만들기

### 실행 구조

```
agenticAI/                       ← 프로젝트 루트
├── .venv/                       ← 공용 가상환경 (이미 있음)
└── practice/
    └── chapter6/
        └── code/
            ├── .env             ← API 키 (이미 있음, GROQ_API_KEY 추가)
            ├── requirements.txt
            └── explainer.py     ← 이번 홈과제 파일
```

터미널에서 실행하는 방법:

```bash
# 프로젝트 루트에서
source .venv/bin/activate

cd practice/chapter6/code
python explainer.py
```

### 준비

```bash
pip install langgraph langchain-groq python-dotenv
```

Groq API 키 발급: https://console.groq.com → 무료 계정 생성 후 API Keys에서 발급

`.env` 파일에 API 키를 넣어둔다:

```
GROQ_API_KEY=gsk_...
```

---

### Step 1. 상태 정의

아래 코드를 `explainer.py`로 저장한다.

> **Copilot 프롬프트**
> ```
> Python TypedDict로 LangGraph 워크플로우 상태를 정의해줘.
> 필드는 topic(str), explanation(str), is_ok(bool), attempt(int).
> dotenv로 환경변수도 로드해줘.
> ```

```python
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

class ExplainerState(TypedDict):
    topic: str
    explanation: str
    is_ok: bool
    attempt: int
```

확인할 것:
- 필드 4개가 각각 무엇을 표현하는지 말로 설명할 수 있는가

---

### Step 2. 노드 작성

이론에서 본 `generate`와 `check` 노드를 그대로 추가한다.

> **Copilot 프롬프트**
> ```
> langchain_groq의 ChatGroq(model="llama-3.3-70b-versatile")를 써서
> ExplainerState를 받는 LangGraph 노드 두 개를 만들어줘.
> generate 노드: topic을 받아 비전공자에게 한 문장 설명을 생성하고
>   explanation과 attempt+1을 반환.
> check 노드: explanation을 보고 비전공자에게 명확한지 yes/no로 판정해서
>   is_ok를 반환.
> 각 노드에 print로 진행 상황을 출력해줘.
> ```

```python
from langchain_groq import ChatGroq

llm = ChatGroq(model="llama-3.3-70b-versatile")

def generate(state: ExplainerState) -> dict:
    prompt = f"'{state['topic']}'을 비전공자에게 한 문장으로 설명해라."
    result = llm.invoke(prompt)
    print(f"[시도 {state['attempt'] + 1}] {result.content}")
    return {
        "explanation": result.content,
        "attempt": state["attempt"] + 1,
    }

def check(state: ExplainerState) -> dict:
    prompt = (
        f"다음 설명이 비전공자에게 명확한가? '{state['explanation']}'\n"
        "명확하면 'yes', 아니면 'no'만 답해라."
    )
    result = llm.invoke(prompt)
    verdict = result.content.strip().lower() == "yes"
    print(f"[판정] {'통과' if verdict else '재생성 필요'}")
    return {"is_ok": verdict}
```

---

### Step 3. 분기와 그래프 조립

> **Copilot 프롬프트**
> ```
> LangGraph StateGraph로 위 노드들을 연결해줘.
> route 함수: is_ok가 True이거나 attempt >= 3이면 'end', 아니면 'generate' 반환.
> 흐름: START → generate → check → route 분기.
> graph.compile()까지 작성해줘.
> ```

```python
from langgraph.graph import StateGraph, END

def route(state: ExplainerState) -> str:
    if state["is_ok"]:
        return "end"
    if state["attempt"] >= 3:
        print("[종료] 최대 시도 횟수 초과")
        return "end"
    return "generate"

builder = StateGraph(ExplainerState)
builder.add_node("generate", generate)
builder.add_node("check", check)
builder.set_entry_point("generate")
builder.add_edge("generate", "check")
builder.add_conditional_edges("check", route, {"end": END, "generate": "generate"})
graph = builder.compile()
```

---

### Step 4. 실행 및 확인

> **Copilot 프롬프트**
> ```
> topic='블록체인'으로 초기 상태를 만들고 graph.invoke()로 실행하는 코드 작성해줘.
> 실행 후 최종 explanation과 총 attempt 횟수를 출력해줘.
> ```

```python
initial_state = {
    "topic": "블록체인",
    "explanation": "",
    "is_ok": False,
    "attempt": 0,
}

result = graph.invoke(initial_state)
print("\n--- 최종 결과 ---")
print(result["explanation"])
print(f"총 시도 횟수: {result['attempt']}")
```

실행 후 확인할 것:

- 몇 번 만에 통과했는가
- `print` 출력에서 분기가 어떻게 흘렀는가
- `topic`을 "양자컴퓨터", "딥러닝"으로 바꿔서 다시 돌려본다

---

### Step 5. 종료 조건 제거해보기

> **Copilot 프롬프트**
> ```
> route 함수에서 attempt >= 3 종료 조건을 제거하면 어떤 일이 생기는지 설명해줘.
> LangGraph가 자동으로 무한 루프를 막아주는가?
> ```

`route` 함수에서 `attempt >= 3` 조건을 주석 처리하고 실행한다.

```python
def route(state: ExplainerState) -> str:
    if state["is_ok"]:
        return "end"
    # if state["attempt"] >= 3:  # ← 이 줄을 주석 처리
    #     return "end"
    return "generate"
```

- 어떤 일이 생기는가
- LangGraph가 자동으로 막아주는가, 아니면 직접 막아야 하는가
- 다시 조건을 복원한다

---

### Step 6. 자유 수정

> **Copilot 프롬프트 예시 (원하는 방향으로 바꿔 입력)**
> ```
> check 노드의 기준을 '초등학생도 이해할 수 있는가'로 바꿔줘.
> ```
> ```
> 최대 시도 횟수를 3회에서 5회로 늘려줘.
> ```

아래 중 하나를 선택해서 수정한다.

**A. 주제 바꾸기**
- `topic`을 관심 있는 단어로 바꿔서 결과를 본다

**B. 기준 바꾸기**
- `check` 노드의 프롬프트를 수정해서 "초등학생도 이해할 수 있는가"로 기준을 높인다
- 통과율이 달라지는지 관찰한다

**C. 시도 횟수 늘리기**
- 최대 시도를 5회로 바꾼다
- 결과가 달라지는가

---

## 제출물

- `explainer.py` 전체 코드
- Step 4 실행 결과 (터미널 출력 캡처)
- Step 5에서 종료 조건을 제거했을 때 어떤 일이 생겼는지 두 줄 설명

---

## 체크리스트

- 상태 객체가 있다
- 노드가 변경된 필드만 반환한다
- 분기 함수가 있다
- 반복 종료 조건이 있다
- 실행 결과를 말로 설명할 수 있다

---

## 심화 읽기

- LangGraph 1.0의 장기 메모리
- LangSmith 기반 추적
- 외부 저장소와의 통합

---

