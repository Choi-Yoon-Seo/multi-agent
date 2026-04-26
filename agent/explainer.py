from typing import TypedDict
from dotenv import load_dotenv
import os

load_dotenv()

try:
    from langchain_groq import ChatGroq
    from langgraph.graph import StateGraph, END
except Exception:
    ChatGroq = None
    StateGraph = None
    END = None


class ExplainerState(TypedDict):
    topic: str
    explanation: str
    is_ok: bool
    attempt: int


def make_llm():
    if ChatGroq is None:
        print("Missing optional dependencies. Install requirements in requirements.txt and try again.")
        return None
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("GROQ_API_KEY not set in environment. Create .env with GROQ_API_KEY=...")
        return None
    return ChatGroq(model="llama-3.3-70b-versatile")


def generate(state: ExplainerState, llm) -> dict:
    prompt = f"'{state['topic']}'을 비전공자에게 한 문장으로 설명해라."
    if llm is None:
        content = f"[MOCK] {state['topic']}를 간단히 설명한 문장"
    else:
        try:
            result = llm.invoke(prompt)
            content = result.content
        except Exception as e:
            print(f"[경고] LLM 호출 실패: {e}. 모드: mock으로 대체합니다.")
            content = f"[MOCK-FALLBACK] {state['topic']}를 간단히 설명한 문장"
    print(f"[시도 {state['attempt'] + 1}] {content}")
    return {
        "explanation": content,
        "attempt": state["attempt"] + 1,
    }


def check(state: ExplainerState, llm) -> dict:
    prompt = (
        f"다음 설명이 비전공자에게 명확한가? '{state['explanation']}'\n"
        "명확하면 'yes', 아니면 'no'만 답해라."
    )
    if llm is None:
        # Simple heuristic: if length > 20 chars consider OK (mock)
        verdict = len(state["explanation"]) > 20
    else:
        try:
            result = llm.invoke(prompt)
            verdict = result.content.strip().lower() == "yes"
        except Exception as e:
            print(f"[경고] LLM 호출 실패(판정): {e}. 모드: mock 판정 사용")
            verdict = len(state["explanation"]) > 20
    print(f"[판정] {'통과' if verdict else '재생성 필요'}")
    return {"is_ok": verdict}


def route(state: ExplainerState) -> str:
    if state["is_ok"]:
        return "end"
    if state["attempt"] >= 3:
        print("[종료] 최대 시도 횟수 초과")
        return "end"
    return "generate"


def build_graph(llm):
    if StateGraph is None:
        return None
    # wrapper nodes that accept only state and return partial updates
    def _generate(state: ExplainerState) -> dict:
        return generate(state, llm)

    def _check(state: ExplainerState) -> dict:
        return check(state, llm)

    builder = StateGraph(ExplainerState)
    builder.add_node("generate", _generate)
    builder.add_node("check", _check)
    builder.set_entry_point("generate")
    builder.add_edge("generate", "check")
    builder.add_conditional_edges("check", route, {"end": END, "generate": "generate"})
    return builder.compile()


def main():
    llm = make_llm()
    graph = build_graph(llm)

    initial_state = {
        "topic": os.getenv("TOPIC", "블록체인"),
        "explanation": "",
        "is_ok": False,
        "attempt": 0,
    }

    if graph is None:
        # Fallback: run simple loop without LangGraph
        print("LangGraph not available — running fallback loop (mock).")
        state = initial_state
        for _ in range(3):
            upd = generate(state, llm)
            state.update(upd)
            upd2 = check(state, llm)
            state.update(upd2)
            if state["is_ok"]:
                break
        print("\n--- 최종 결과 ---")
        print(state["explanation"])
        print(f"총 시도 횟수: {state['attempt']}")
        return

    result = graph.invoke(initial_state)
    print("\n--- 최종 결과 ---")
    print(result["explanation"])
    print(f"총 시도 횟수: {result['attempt']}")


if __name__ == "__main__":
    main()
