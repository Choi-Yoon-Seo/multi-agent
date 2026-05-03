# Week 13. HITL·배포·관측·비용 + 최종 프로젝트 가이드라인

> 강의 + 수업 HITL 실습 + Homework 최종 프로젝트 설계서
> 참조: LangGraph `interrupt`/`Command`, LangSmith, OpenAI/Groq 비용 로그
> Docker는 심화·선택 (13.7)

---

## 학습 목표

- LangGraph `interrupt`로 사람 승인(HITL)을 멀티에이전트에 끼워 넣는다
- LangSmith로 트레이스를 보고, 응답·토큰·비용을 관측한다
- 모델 라우팅·프롬프트 캐싱 같은 비용 최적화 기법을 안다
- **최종 프로젝트(14~15주차) 가이드라인**을 이해하고 설계서 초안을 시작한다
- (심화) 12주차 RAG 멀티에이전트를 **Docker 이미지**로 만든다

---

## 이번 주 핵심 원칙

- 2회차 90분 안에 다음 셋이 핵심: **HITL 승인 + 비용 로그 + 설계서 초안**
- Docker는 *심화/선택*. 시간이 남는 학생만, 또는 14주차 1:1 상담 슬롯에서 보충
- 새 개념은 “HITL + 관측 + 비용” 셋뿐 — 모두 *기존 시스템 위에 얹는다*

---

## 13.1 사람 승인이 왜 필요한가

12주차의 출처 검증 게이트는 *모델*이 모델을 검증했다. 그래도 다음 작업에는 부족하다.

| 상황 | 자동만 두면 위험한 이유 |
|---|---|
| 결제·환불 | 금전 피해 직접 발생 |
| 파일/DB 삭제 | 복구 어려움 |
| 외부 메시지 발송 (이메일·슬랙·SNS) | 신뢰·평판 영향 |
| 인사·채점 등 윤리적 판단 | 책임 소재 |

이런 작업에는 **사람이 마지막 결정**을 한다. 그것이 HITL이다.

### HITL의 4가지 패턴

| 패턴 | 의미 | 예시 |
|---|---|---|
| Approval | 실행 전 승인 | “이 SQL을 정말 실행할까요?” |
| Review | 실행 후 검토 | 모델이 작성한 PR을 사람이 머지 |
| Edit | 사람이 직접 수정 후 진행 | 답변 초안을 사람이 손봐서 발송 |
| Escalation | 모델이 자신 없으면 사람에게 이관 | 챗봇 → 상담원 |

이번 주 실습에서는 **Approval** 패턴을 다룬다.

---

## 13.2 LangGraph `interrupt`로 승인 노드 만들기

LangGraph 1.0의 `interrupt`는 그래프 실행을 *그 자리에서 멈추고*, 외부(사람)의 입력을 기다린다.

```python
from langgraph.types import interrupt, Command

def approval_node(state):
    # 사람에게 보여줄 정보를 dict로 넘기고, 그래프를 일시 정지
    decision = interrupt({
        "draft": state["draft"],
        "research": state["research"][:200],
    })
    # 외부에서 Command(resume=...)로 재개하면 decision이 그 값으로 채워진다
    if decision == "approve":
        return {"messages": ["[승인] 사람 승인 통과"]}
    return Command(goto="writer", update={"draft": "", "messages": [f"[거부] {decision}"]})
```

호출 측은 두 단계다.

```python
# 1) 그래프 실행 — interrupt에서 멈춘다
result = graph.invoke(initial_state, config=config)
# result는 멈춘 지점의 정보를 담는다

# 2) 사람이 결정한 뒤 재개
graph.invoke(Command(resume="approve"), config=config)
```

처음 구현에서는 *터미널 입력*으로 사람 결정을 받는다.

---

## 13.3 만드는 것 (필수)

12주차 RAG 멀티에이전트에 **승인 노드**를 추가하고, **비용 로그**를 남긴다.

```text
[질문] → [Supervisor] → [search] → [writer] → [grounding]
                                                   ↓
                                       PASS    [approval]    FAIL → writer
                                                   ↓
                                          (사람 승인 입력)
                                                   ↓
                                              [최종 답변]
```

(심화·선택) 전체 시스템을 **Docker**로 묶어 동료 노트북에서도 돌리게 만든다 — 13.7 참조.

---

## 13.4 실행 환경

12주차까지 사용한 `multi-agent/` 폴더를 그대로 이어서 쓴다. 주차별 새 폴더를 만들지 않는다.

```bash
source .venv/bin/activate
cd multi-agent

cp rag_supervisor.py agent.py

pip install langsmith
```

---

## 13.5 수업 실습: HITL 승인과 비용 로그 추가

수업 예시는 12주차 RAG 멀티에이전트에 승인 노드와 비용 로그를 추가하는 것이다. 완성 예시는 아래 파일에 정리한다.

```text
multi-agent/docs/week13_inclass_hitl.md
```

Homework는 최종 프로젝트 설계서 초안을 별도로 작성한다.

```text
multi-agent/docs/week13_homework_project_plan.md
```

### Step 1. 승인 노드 추가

### Step 1. 승인 노드 추가

> **Copilot 프롬프트**
> ```
> agent.py에 approval_node를 추가한다.
> grounding이 PASS면 approval_node로 보내고,
> approval_node는 interrupt를 호출해 draft와 출처 청크 일부를 사람에게 보여준다.
> 사람이 "approve"를 입력하면 END.
> "rewrite: <피드백>"을 입력하면 messages에 피드백을 남기고 writer로 돌아간다.
> ```

```python
from langgraph.types import interrupt

def approval_node(state):
    decision = interrupt({
        "draft": state["draft"],
        "preview_chunks": state["research"][:300],
        "instructions": "approve / rewrite: <피드백> 중 하나를 입력",
    })
    if decision.strip().lower() == "approve":
        return {"messages": ["[승인] 사람 승인"]}
    return Command(
        goto="writer",
        update={
            "draft": "",
            "messages": [f"[거부] {decision}"],
        },
    )
```

`grounding`을 다음처럼 수정한다.

```python
def grounding_check(state):
    # ...
    if verdict.upper().startswith("PASS"):
        return Command(goto="approval", update={"messages": ["[검증] PASS"]})
    return Command(goto="writer", update={"draft": "", "messages": [f"[검증] FAIL"]})
```

`builder`에 승인 노드 등록:

```python
builder.add_node("approval", approval_node)
# approval은 Command로 다음을 결정하므로 add_edge 불필요
```

### Step 2. 호출 측: 사람 입력 받기

> **Copilot 프롬프트**
> ```
> main 부분을 수정한다.
> 1) graph.invoke(initial_state, config) 호출
> 2) 결과에 __interrupt__가 있으면 그 정보를 출력하고 input()으로 사람 결정 받음
> 3) graph.invoke(Command(resume=user_input), config)로 재개
> 4) 최종 draft 출력
> ```

```python
from langgraph.types import Command

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "hitl-1"}, "recursion_limit": 16}
    state = graph.invoke(initial_state, config=config)

    while "__interrupt__" in state:
        info = state["__interrupt__"][0].value
        print("\n=== 승인 요청 ===")
        print("초안:\n", info["draft"])
        print("\n근거 청크 미리보기:\n", info["preview_chunks"])
        decision = input("\n결정 (approve / rewrite: ...): ").strip()
        state = graph.invoke(Command(resume=decision), config=config)

    print("\n=== 최종 답변 ===")
    print(state["draft"])
```

학생은 이때 직접 “approve” 또는 “rewrite: 더 짧게 부탁” 같은 명령을 친다.

---

## 13.6 관측: LangSmith + 비용 로그

### LangSmith 트레이스

`.env`의 `LANGSMITH_TRACING=true`만 켜져 있으면 자동으로 보인다. 다음을 확인한다.

| 보는 항목 | 어디서 |
|---|---|
| 전체 흐름 | Trace 트리 (supervisor, search, analyst, writer, grounding, approval) |
| 입력/출력 토큰 | 각 LLM 호출 노드 |
| 응답 시간 | 각 노드의 latency |
| 인터럽트 지점 | approval 노드의 일시 정지 표시 |

### Streaming — 진행 상황을 실시간으로 보기

`graph.invoke()` 대신 `graph.stream()`을 쓰면 노드 결과가 *나오는 즉시* 받아 볼 수 있다. 데모에서 “기다리는 시간”을 줄이는 도구다.

```python
for event in graph.stream(initial_state, config=config, stream_mode="updates"):
    for node, payload in event.items():
        print(f"⟶ {node}: {list(payload.keys())}")
```

`stream_mode`:
- `"updates"` — 노드별 결과 (가장 자주 쓰임)
- `"values"` — 매 노드 후 *전체 상태*
- `"messages"` — 토큰 단위 LLM 출력 (스트리밍 답변)

최종 프로젝트 데모에서 `stream` + `messages` 모드를 쓰면 답변이 *타이핑되듯이* 흐른다.

### 간단한 비용 로그

> **Copilot 프롬프트**
> ```
> 각 LLM 호출 후 응답 객체의 usage_metadata(input_tokens, output_tokens)를
> messages에 기록한다.
> 마지막에 전체 토큰 합계와 추정 비용을 출력한다.
> Groq llama-3.3-70b-versatile 단가는 시연용으로 input $0.59 / output $0.79 per 1M token로 가정.
> ```

```python
INPUT_PRICE = 0.59 / 1_000_000
OUTPUT_PRICE = 0.79 / 1_000_000

def track(label, response):
    md = getattr(response, "usage_metadata", None) or {}
    inp, outp = md.get("input_tokens", 0), md.get("output_tokens", 0)
    cost = inp * INPUT_PRICE + outp * OUTPUT_PRICE
    return f"[{label}] in={inp} out={outp} cost=${cost:.6f}", cost
```

각 노드에서 `llm.invoke(...)` 결과를 `track`으로 감싼다. 마지막에 합계를 출력한다.

운영 환경에서는 LangSmith의 “Cost” 패널을 쓰지만, *어떻게 계산되는지* 한 번은 직접 만들어 본다.

---

## 13.7 (심화·선택) Docker 컨테이너화

> 시간이 남는 학생, 또는 14주차 1:1 상담에서 보충하고 싶은 학생만.
> 최종 프로젝트의 “통합 요소 2개+” 평가 항목을 채우는 한 가지 옵션이다.

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent.py .
COPY docs/ docs/
COPY vectorstore/ vectorstore/
CMD ["python", "agent.py"]
```

`.dockerignore`:
```
.venv
__pycache__
*.pyc
.env
```

### 빌드와 실행

```bash
docker build -t rag-agent:w13 .

docker run --rm -it \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  -e LANGSMITH_API_KEY=$LANGSMITH_API_KEY \
  -e LANGSMITH_TRACING=true \
  -e LANGSMITH_PROJECT=week13-deploy \
  rag-agent:w13
```

`-it`로 사람 입력(approval)을 받을 수 있게 한다. API 키는 `-e`로 주입 — 이미지에 *절대 굽지 않는다*.

### 검증 포인트

- 다른 학생 노트북에서 같은 이미지로 실행 가능한가
- API 키 없이 실행 시 에러가 *명확하게* 나는가
- 로그에 비밀이 새지 않는가

---

## 13.8 비용 최적화 개념 (개념만)

이번 주에는 다음 셋을 중심으로 본다.

### (1) 모델 라우팅

쉬운 질문은 작은 모델, 어려운 질문은 큰 모델로 보낸다.

```python
def pick_model(question):
    if len(question) < 50 and "?" in question:
        return ChatGroq(model="llama-3.1-8b-instant")
    return ChatGroq(model="llama-3.3-70b-versatile")
```

### (2) 프롬프트 캐싱

긴 시스템 프롬프트나 많은 청크를 매번 다시 보내지 않는다. Anthropic·OpenAI는 캐시 단가를 따로 매긴다 (입력 단가의 10~25%).

처음에는 “같은 시스템 프롬프트는 한 번만 정의해서 재사용”하는 것부터 적용한다.

### (3) 적응형 추론

답이 자명하면 짧게, 어려우면 길게 생각하게 한다 (`reasoning_effort` 또는 자체 분기).

---

## 13.9 자주 만나는 실수

### 필수 흐름

| 증상 | 원인 | 해결 |
|---|---|---|
| `interrupt`가 안 멈춘다 | resume 처리 안 함 | 호출 측에서 `Command(resume=...)`로 재개 |
| approve 입력했는데 다시 묻는다 | 비교 시 공백·대소문자 | `decision.strip().lower() == "approve"` |
| LangSmith 트레이스 안 잡힘 | 환경변수 미적용 | `.env` 다시 로드, `LANGSMITH_TRACING=true` |
| 비용 합계가 0 | 모델이 usage_metadata 미반환 | 모델 버전 확인 또는 `response_metadata` 사용 |
| recursion 끝없이 돈다 | `recursion_limit` 미설정 | config에 12~16으로 제한 |

### Docker 심화 (선택)

| 증상 | 원인 | 해결 |
|---|---|---|
| Docker에서 vectorstore가 안 보인다 | COPY 누락 | Dockerfile에 `COPY vectorstore/ vectorstore/` |
| 컨테이너 내부에서 input()이 안 됨 | `-it` 누락 | `docker run -it` |
| API 키 노출 | `.env`를 이미지에 넣음 | `.dockerignore`로 제외, `-e`로 주입 |

---

## 13.10 최종 프로젝트 가이드라인 (30분)

여기서부터 강의가 아니라 **프로젝트 시작 시간**이다.

### 일정

| 시점 | 할 일 |
|---|---|
| 13주차 (이번 주) | 주제 확정 + 설계서 초안 |
| 14주차 | 집중 개발 + 1:1 상담 |
| 15주차 | 발표 (10분 발표 + 5분 질의응답) |

### 평가 기준 (재공지)

| 항목 | 비중 |
|---|---|
| MCP 서버 구현 | 20% |
| 멀티에이전트 워크플로우 | 30% |
| 통합 요소 (RAG·HITL·배포 중 2개 이상) | 20% |
| 발표 및 구두 평가 | 20% |
| 코드 품질 | 10% |

15주차 발표가 **기말고사를 대체**한다. 5분 질의응답이 구두 평가다.

### 주제 선정 원칙

1. **자기 도메인** (관심 분야·전공·취미)에서 고른다 — 동기가 약하면 14주차에 막힌다
2. **2주 안에 끝낼 수 있는 범위** — 욕심 내지 않는다
3. **9주차 설계표를 재활용** — 이미 역할 분리 1개를 했다
4. **출처가 분명한 도메인** 선호 — 12주차 RAG가 자연스럽게 결합

### 주제 예시 (반드시 고를 필요 없음)

1. 학과 공지 자동 요약 멀티에이전트 (크롤링 → 요약 → 검토 + HITL 승인)
2. 코드 리뷰 자동화 봇 (GitHub 이슈 → Copilot → 사람 승인 + 로그)
3. 논문 검색·분석 멀티에이전트 (검색 → 분석 → 보고서, 출처 표기)
4. 고객 지원 분류·답변 멀티에이전트 (분류 → RAG 답변 → 에스컬레이션)
5. 데이터 분석 멀티에이전트 (CSV 로드 → 분석 → 시각화 → 검증)

### 설계서 초안 양식 (이번 주 제출)

```markdown
## 최종 프로젝트 설계서 (초안)

1. 제목:
2. 한 문장 설명:
3. 풀려는 문제 (왜 단일 에이전트로 부족한가):
4. 시스템 아키텍처
   - MCP 서버: 어떤 도구/리소스를 노출하는가
   - 에이전트 역할: (Supervisor + N명, 각자 책임)
   - 통합 요소: RAG / HITL / 배포 중 2개 이상 선택
5. 데이터/문서 출처 (RAG가 있다면):
6. HITL 지점:
7. 평가 방법: 어떻게 “잘 됐다”를 보일 것인가
8. 14주차 일정 (3일 단위):
9. 가장 큰 위험 1개와 대응:
```

---

## 13.11 제출물

### 필수 (90분 안에 끝낼 수 있는 양)

- 수업 실습 파일: `multi-agent/docs/week13_inclass_hitl.md`
- Homework 파일: `multi-agent/docs/week13_homework_project_plan.md`
- `agent.py` (HITL 승인 노드 + 비용 로그 추가본)
- HITL 흐름 캡처 — “approve” 한 번 + “rewrite: ...” 한 번
- LangSmith 트레이스 캡처 (또는 트레이스 ID)
- 비용 로그 출력
- **최종 프로젝트 설계서 초안** (위 양식)

### 선택 (가산점)

- Dockerfile + `docker run` 실행 캡처
- 다른 학생 노트북에서 이미지 실행 성공 캡처

### 회고 질문

1. HITL 승인 노드가 의미 있게 작동한 사례는 무엇이었는가
2. LangSmith 트레이스에서 가장 비용이 큰 노드는 어디였는가
3. 비용을 줄인다면 어디부터 손볼 것인가
4. (Docker를 했다면) 다른 사람 환경에서 돌릴 때 무엇이 막혔는가
5. 최종 프로젝트 설계서에서 가장 자신 없는 부분은 무엇인가

---

## 체크리스트

- LangGraph `interrupt`로 사람 승인 노드를 만들 수 있다
- HITL의 4가지 패턴을 구분한다
- LangSmith로 트레이스·토큰·비용을 본다
- 모델 라우팅·프롬프트 캐싱의 개념을 안다
- (선택) 멀티에이전트 시스템을 Docker로 묶을 수 있다
- 최종 프로젝트 설계서 초안을 가지고 14주차에 들어간다

---

## 참고 자료

- LangGraph HITL 가이드: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- LangGraph `interrupt` API: https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt
- Docker 공식: https://docs.docker.com/get-started/
- LangSmith Observability: https://docs.smith.langchain.com/observability
- Anthropic Prompt Caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- OpenAI Prompt Caching: https://platform.openai.com/docs/guides/prompt-caching

---

## 다음 주 예고

14주차는 강의가 없다. **개인 프로젝트 집중 개발**과 교수 1:1 상담 슬롯을 운영한다. 15주차에 10분 발표 + 5분 질의응답으로 평가한다.
