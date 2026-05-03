# Week 12. 멀티에이전트 + RAG·메모리 통합과 신뢰성

> 강의 + 수업 RAG 실습 + Homework RAG 변형 과제
> 참조: LangChain Vector RAG, Self-Consistency (Wang et al.), 에이전트 메모리 4유형

---

## 학습 목표

- RAG가 왜 필요한지 설명한다 (지식 컷오프·환각·출처 추적)
- 인덱싱·청킹·임베딩·검색의 흐름을 이해한다
- 에이전트 메모리 4유형(Working·Episodic·Semantic·Procedural)의 차이를 안다
- 환각을 줄이는 두 가지 검증(Self-Consistency, 출처 일치)을 적용한다
- 10주차의 Supervisor 시스템에 **검색 에이전트**를 추가하여 RAG 멀티에이전트로 확장한다
- 답변에 출처를 남기고, 출처 검증 가드레일을 통과시킨다

---

## 이번 주 핵심 원칙

- “정답이 그럴듯한가”가 아니라 “**근거가 있는가**”를 본다
- 단일 RAG가 아니라 **멀티에이전트의 한 단계로서의 RAG**를 다룬다
- 이번 주에는 벡터 RAG 한 가지에 집중한다 (그래프 RAG는 심화 읽기)

---

## 12.1 RAG가 왜 필요한가

LLM 단독은 다음 문제를 가진다.

| 문제 | 예시 |
|---|---|
| 지식 컷오프 | 최근 사건/내부 문서를 모른다 |
| 환각 | 자신 있게 거짓을 말한다 |
| 출처 부재 | 왜 그렇게 답했는지 추적할 수 없다 |

RAG의 기본 아이디어는 단순하다.

```text
[질문] ──→ [관련 문서 검색] ──→ [검색된 문서 + 질문] ──→ [LLM 답변]
                                                              │
                                                              ▼
                                                         [출처 표기]
```

핵심: **모델이 모든 지식을 외우고 있을 필요가 없다.** 필요할 때 찾아서 답한다.

---

## 12.2 RAG의 두 단계

### 단계 1. 인덱싱 (저장)

```text
[원본 문서] ─→ [청킹] ─→ [임베딩] ─→ [벡터 저장소]
```

- **청킹**: 긴 문서를 작은 조각으로 쪼갠다. 너무 크면 관련 없는 내용이 섞이고, 너무 작으면 문맥이 끊긴다. 처음에는 *고정 크기 청킹*(예: 500자)부터 시작한다.
- **임베딩**: 텍스트를 숫자 벡터로 바꾼다. 비슷한 의미는 비슷한 벡터가 된다.
- **벡터 저장소**: 벡터를 저장하고, 비슷한 것을 빠르게 찾을 수 있게 한다 (FAISS, Chroma, pgvector).

### 단계 2. 검색-생성

```text
[질문] ─→ [임베딩] ─→ [유사도 검색] ─→ [상위 k개 청크] ─→ [LLM] ─→ [답변 + 출처]
```

핵심 파라미터:
- `k`: 상위 몇 개를 가져올지 (보통 3~5)
- 프롬프트에 “이 청크 외의 정보는 사용하지 말 것”을 명시

---

## 12.3 에이전트 메모리 4유형

RAG는 “**Semantic Memory**”에 해당한다. 전체 그림은 다음과 같다.

| 유형 | 무엇을 기억하는가 | 이번 실습에서의 형태 |
|---|---|---|
| Working | 지금 진행 중인 대화·계산 | LangGraph의 `state` |
| Episodic | 과거에 있었던 일 (대화 이력) | Checkpointer의 thread 기록 (10주차) |
| Semantic | 외부 지식 (사실·문서) | **벡터 저장소 = RAG** (이번 주) |
| Procedural | 어떻게 하는지 (절차·도구 사용법) | 시스템 프롬프트, Skill 문서 |

여기서는 4유형의 차이를 구분하고, 12주차에서는 Semantic Memory를 직접 다룬다.

---

## 12.4 환각과 두 가지 검증

환각의 유형 (이름만):

| 유형 | 한 줄 |
|---|---|
| 사실 오류 | 잘못된 사실을 자신 있게 말함 |
| 논리 오류 | 전제와 결론이 안 맞음 |
| 출처 조작 | 없는 논문/URL을 인용 |

검증 도구 두 가지:

| 도구 | 어떻게 |
|---|---|
| Self-Consistency | 같은 질문을 *여러 번* 묻고, 답이 갈리면 신뢰도 낮음으로 처리 |
| **출처 일치 검증** | 답변의 모든 문장이 *검색된 청크*에 있는지 LLM이 확인 — 이번 주 실습의 핵심 |

이번 주 실습은 **출처 일치 검증**을 *Pydantic 구조화 출력*으로 만든다 (Step 3).

---

## 12.5 만드는 것

10주차의 Supervisor 시스템에 **검색 에이전트**를 추가한다.

```text
[질문]
   ↓
[Supervisor]
   /     |     \
 [검색]  [분석가]  [작성자]
   │       │        │
   └───────┴────────┘
            ↓
       [출처 검증 게이트]
            ↓
        [최종 답변 + 출처]
```

검색 에이전트는 벡터 저장소에서 관련 청크를 찾아 `research`에 채워 넣는다. 작성자는 검색된 청크 *외의 정보를 쓰지 않도록* 강제된다. 마지막에 출처 검증 게이트가 답변을 통과시킬지 결정한다.

---

## 12.6 실행 환경

9~10주차에서 이어 쓰던 루트 가상환경과 `multi-agent/` 폴더를 그대로 사용한다.

```bash
source .venv/bin/activate
cd multi-agent

pip install langgraph langchain-groq langchain-community langchain-huggingface \
            sentence-transformers faiss-cpu python-dotenv
```

`.env`는 10주차와 동일.

> Groq API는 임베딩을 제공하지 않으므로, 임베딩은 로컬 **HuggingFace `sentence-transformers/all-MiniLM-L6-v2`**를 쓴다. 인터넷 연결이 어려운 환경에서는 OpenAI Embeddings로 바꿀 수 있다.

---

## 12.7 수업 실습: RAG 검색 에이전트 추가

수업 예시는 제공된 문서 3개를 인덱싱하고, 검색 에이전트가 가져온 청크만 근거로 답변하게 만드는 것이다. 완성 예시는 아래 파일에 정리한다.

```text
multi-agent/docs/week12_inclass_rag.md
```

Homework는 각자 다른 작은 문서 묶음을 선택해 같은 구조로 만든다.

```text
multi-agent/docs/week12_homework_rag.md
```

### Step 1. 문서 다운로드 + 인덱싱

문서 3개는 *수업 저장소에서 미리 제공*한다. 학생은 다운로드 후 인덱싱만 한다.

```bash
# 수업 저장소(예시)에서 받기
cp -r ../class_assets/week12/docs ./docs
```

(또는 교수가 GitHub 링크로 배포)

> **Copilot 프롬프트**
> ```
> index.py 파일을 만들어줘.
> docs/ 안의 .md 파일을 모두 읽어
> RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)로 청킹,
> HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")로 임베딩,
> FAISS로 ./vectorstore에 저장.
> 청크 수와 첫 청크 미리보기를 출력한다.
> ```

```python
# index.py
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

docs = []
for md in Path("docs").glob("*.md"):
    docs += TextLoader(str(md), encoding="utf-8").load()

chunks = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50
).split_documents(docs)
print(f"청크 수: {len(chunks)}")

vs = FAISS.from_documents(
    chunks,
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
)
vs.save_local("vectorstore")
print("저장 완료")
```

한 번 실행해 `vectorstore`를 만든다. (1~2분)

### Step 2. 검색 에이전트 추가 + Supervisor 라우팅 갱신

10주차의 `supervisor.py`를 복사해 `rag_supervisor.py`로 만든 뒤, 검색 노드를 *기존 Supervisor*에 한 줄 추가한다.

```python
# rag_supervisor.py 상단에 추가
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

vectorstore = FAISS.load_local(
    "vectorstore",
    HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    allow_dangerous_deserialization=True,
)

def search_agent(state: TeamState) -> dict:
    docs = vectorstore.similarity_search(state["question"], k=3)
    formatted = "\n\n".join(
        f"[출처: {Path(d.metadata.get('source', '?')).name}]\n{d.page_content}"
        for d in docs
    )
    return {
        "research": formatted,
        "messages": [f"[검색] {len(docs)}개 청크"],
    }
```

10주차의 **`Route` Pydantic 모델**과 **시스템 프롬프트**에 `search` 선택지를 추가한다. 구조화 출력 덕분에 손볼 곳은 두 군데뿐이다.

```python
from typing import Literal
from pydantic import BaseModel, Field

class Route(BaseModel):
    """Supervisor가 다음에 호출할 에이전트."""
    next: Literal["search", "analyst", "writer", "FINISH"] = Field(
        description="다음 단계로 보낼 에이전트. 외부 자료가 필요하면 search."
    )

router_llm = llm.with_structured_output(Route)

SUPERVISOR_SYSTEM = """\
너는 RAG 멀티에이전트의 supervisor다.

규칙:
- research가 비어 있으면 search (외부 문서에서 청크를 가져온다)
- analysis 안에 RESEARCH_NEEDED가 있으면 search (다시 검색)
- research가 있고 analysis가 비어 있으면 analyst
- analysis가 있고 draft가 비어 있으면 writer
- draft가 채워져 있으면 FINISH
"""
```

기존 `supervisor` 함수의 호출은 그대로다 — `route.next`가 `"researcher"` 대신 `"search"`를 돌려준다.

`builder`에 노드 등록을 한 줄 추가:

```python
builder.add_node("search", search_agent)
builder.add_edge("search", "supervisor")
# 기존 researcher 노드는 search로 대체되었으므로 등록을 빼거나 그대로 두어도 무방
```

### Step 3. 작성자 강화 + 출처 검증 게이트 (구조화 출력)

`writer`는 **청크 외 정보 금지**. `grounding`은 LLM 판정인데, 출력이 어긋나지 않도록 **Pydantic 구조화 출력**을 쓴다.

```python
from pydantic import BaseModel, Field

class Verdict(BaseModel):
    """출처 검증 결과."""
    passed: bool = Field(description="모든 사실 문장이 청크에서 확인되면 True")
    reason: str = Field(description="판단 사유 한 줄")

verdict_llm = llm.with_structured_output(Verdict)

def writer(state: TeamState) -> dict:
    prompt = (
        "아래 청크의 내용만 사용해 학부생용 한국어 답변을 만들어라. "
        "청크에 없는 사실은 절대 만들지 마라. "
        "각 사실 문장 끝에 [출처: 파일명]을 표시하라.\n\n"
        f"질문: {state['question']}\n\n청크:\n{state['research']}"
    )
    return {
        "draft": llm.invoke(prompt).content,
        "messages": ["[작성자] 출처 포함 초안"],
    }

def grounding(state: TeamState) -> Command:
    v: Verdict = verdict_llm.invoke(
        "다음 답변의 모든 사실 문장이 청크에서 직접 확인 가능한지 판단해라.\n\n"
        f"답변: {state['draft']}\n\n청크:\n{state['research']}"
    )
    print(f"[게이트] passed={v.passed} | {v.reason}")
    if v.passed:
        return Command(goto=END, update={"messages": [f"[게이트] PASS — {v.reason}"]})
    return Command(
        goto="writer",
        update={"draft": "", "messages": [f"[게이트] FAIL — {v.reason}"]},
    )
```

`builder`에 게이트 등록 — `writer` 다음에 게이트가 오게 한다.

```python
builder.add_node("grounding", grounding)
builder.add_edge("writer", "grounding")
# grounding이 Command로 직접 다음을 정함
```

### Step 4. 실행: 정상 질문 + 환각 유도

```python
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "rag-1"}, "recursion_limit": 12}

    # (1) 정상: docs에 있는 주제
    print("\n=== 정상 질문 ===")
    r1 = graph.invoke({
        "messages": [], "question": "LangGraph 1.0의 핵심 변경점을 정리해줘.",
        "research": "", "analysis": "", "draft": "", "next": "",
    }, config=config)
    print(r1["draft"])

    # (2) 환각 유도: docs에 없는 주제
    print("\n=== 환각 유도 ===")
    config2 = {"configurable": {"thread_id": "rag-2"}, "recursion_limit": 12}
    r2 = graph.invoke({
        "messages": [], "question": "2024년 K-pop 차트 1위는?",
        "research": "", "analysis": "", "draft": "", "next": "",
    }, config=config2)
    print(r2["draft"])
    print("\n메시지:", r2["messages"][-3:])
```

학생이 직접 보아야 할 것:
1. search 청크가 질문과 무관하다
2. writer가 “자료에 없다”고 답하거나 환각을 만든다
3. 게이트가 FAIL을 내고 writer로 돌아간다
4. `recursion_limit`에 걸려 결국 종료된다

이 흐름이 **출처 검증의 의미**다.

### Step 5. 분석 메모

5문장으로 다음을 정리한다.

- 청크가 질문에 잘 맞은 사례 1개
- 청크가 빗나간 사례 1개
- 게이트가 잡은 환각 사례 1개 (있으면)
- 게이트가 *놓친* 환각 사례 (있으면) — 가장 중요

---

## 12.8 자주 만나는 실수

| 증상 | 원인 | 해결 |
|---|---|---|
| 검색 결과가 항상 같다 | 청크가 너무 적거나 chunk_size가 너무 큼 | `chunk_size`를 줄이거나 문서를 늘림 |
| 작성자가 청크 밖 사실을 만든다 | 프롬프트의 제약이 약함 | “청크에 없으면 ‘자료에 없다’라고 적어라” 추가 |
| 출처 표기가 제멋대로 | 형식 미지정 | 프롬프트에 정확한 형식 예시 |
| 검증 게이트가 너무 엄격 | yes/no 단답이 아닌 긴 사유 출력 | 프롬프트에 “PASS/FAIL 후 한 줄” 강제 |
| 무한 재시도 | recursion_limit 미설정 | 8~12로 제한 |

---

## 12.9 제출물

### 필수 (90분 안에 끝낼 수 있는 양)

- 수업 실습 파일: `multi-agent/docs/week12_inclass_rag.md`
- Homework 파일: `multi-agent/docs/week12_homework_rag.md`
- `index.py`, `rag_supervisor.py` 코드
- 정상 질문 결과 (출처 표기 포함)
- 환각 유도 결과 (FAIL → 재작성 흐름)
- Step 5 분석 메모 5문장

### 회고 질문

1. 검색 청크의 품질이 답변 품질을 어떻게 좌우했는가
2. 출처 검증 게이트가 잡은 환각 사례는 무엇이었는가
3. 청크 크기를 바꾸면 어떻게 달라졌는가
4. 10주차의 Supervisor와 비교해 무엇이 추가됐는가
5. 이 시스템에 사람의 승인 단계를 넣는다면 어디가 적절한가 (13주차 예고)

---

## 체크리스트

- 인덱싱·청킹·임베딩·검색의 흐름을 자기 코드 위에서 설명한다
- 메모리 4유형의 차이를 한 줄씩 설명한다
- Self-Consistency와 출처 일치 검증을 구분한다
- LangGraph Supervisor에 검색 에이전트를 추가했다
- 답변에 출처가 남고, 출처 검증 게이트가 작동한다
- 환각 사례를 자기 코드로 *직접* 본 경험이 있다

---

## 참고 자료

- LangChain RAG 튜토리얼: https://python.langchain.com/docs/tutorials/rag/
- FAISS: https://github.com/facebookresearch/faiss
- Sentence Transformers: https://www.sbert.net/
- Self-Consistency 논문: Wang et al., 「Self-Consistency Improves Chain of Thought Reasoning in Language Models」 (2022)
- 에이전트 메모리 정리: https://langchain-ai.github.io/langgraph/concepts/memory/

### 심화 (선택)
- GraphRAG: https://github.com/microsoft/graphrag
- LightRAG: https://github.com/HKUDS/LightRAG

---

## 다음 주 예고

13주차에는 이 RAG 멀티에이전트에 **사람 승인(HITL)**을 결합하고, **Docker 컨테이너**로 실행하며, **LangSmith 트레이싱**과 **비용 로그**를 본다. 그리고 1회차 끝부분에 **최종 프로젝트 가이드라인 30분**을 진행한다 — 14~15주차 개인 프로젝트 준비 시작.
