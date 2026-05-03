# Week 7. 미니 프로젝트: 날씨 요약 에이전트 (중간고사 대체)

## 학습 목표

- 4~6주차에 배운 MCP 서버, 도구 호출, LangGraph를 하나로 통합한다
- 도시 이름을 입력하면 날씨를 조회하고 한 문장으로 요약한다
- 요약 품질을 검증하고, 부족하면 다시 생성한다

---

## 이번 주 운영 원칙

- 이번 주 미니 프로젝트가 **중간고사를 대체**한다
- 새로운 개념을 추가하지 않는다 — 4~6주차 내용만 쓴다
- 완성도를 우선한다 — 작고 잘 돌아가는 것이 낫다

---

## 만드는 것

> 도시 이름을 입력하면 날씨 API로 현재 날씨를 조회하고,  
> LLM이 한 문장 요약을 생성한다.  
> 요약이 부족하면 최대 3회까지 다시 생성하고 종료한다.

```
[도시 이름 입력]
      ↓
[fetch_weather 노드]  ← Open-Meteo API 호출 (MCP 도구)
      ↓
[summarize 노드]      ← LLM이 날씨 데이터를 한 문장으로 요약
      ↓
[check 노드]          ← 요약이 도시명과 날씨 정보를 포함하는지 검증
      ↓
[route 분기]          ← 통과 → 종료 / 부족 → 재요약 (최대 3회)
      ↓
[최종 요약 출력]
```

---

## 실행 구조

```
agenticAI/                       ← 프로젝트 루트
├── .venv/                       ← 공용 가상환경 (이미 있음)
└── practice/
    └── chapter7/
        └── code/
            ├── .env             ← API 키 (GROQ_API_KEY, 이미 있음)
            ├── requirements.txt
            ├── weather_tool.py  ← Step 1: 날씨 도구
            └── agent.py         ← Step 2~5: LangGraph 워크플로우
```

터미널에서 실행하는 방법:

```bash
# 프로젝트 루트에서
source .venv/bin/activate

cd practice/chapter7/code
python agent.py
```

패키지 설치 (처음 한 번):

```bash
pip install langgraph langchain-groq httpx python-dotenv
```

---

## 제작 순서

### Step 1. 날씨 도구 만들기

Open-Meteo는 API 키 없이 쓸 수 있는 무료 날씨 API다.

> **Copilot 프롬프트**
> ```
> weather_tool.py 파일을 만들어줘.
> httpx를 써서 Open-Meteo API로 도시 날씨를 가져오는 get_weather(city) 함수를 작성해줘.
> 먼저 geocoding-api.open-meteo.com으로 도시명을 위도/경도로 변환하고,
> api.open-meteo.com으로 current_weather를 조회해서
> city, temperature, windspeed, weathercode를 딕셔너리로 반환해줘.
> 도시를 찾지 못하면 {"error": "..."} 형태로 반환해줘.
> docstring에 이 함수를 언제 써야 하는지 명시해줘.
> ```

Copilot이 생성한 코드를 `weather_tool.py`로 저장한다. 함수 단독으로 먼저 실행해서 결과를 확인한다.

```python
# weather_tool.py
import httpx

def get_weather(city: str) -> dict:
    """
    도시 이름을 받아 현재 기온과 날씨 코드를 반환한다.
    도시명이 잘못되었거나 API 응답이 없으면 오류 메시지를 반환한다.
    """
    # 1) 도시 → 위도/경도 변환
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo = httpx.get(geo_url, params={"name": city, "count": 1}, timeout=5).json()

    if not geo.get("results"):
        return {"error": f"도시를 찾을 수 없습니다: {city}"}

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    # 2) 날씨 조회
    weather_url = "https://api.open-meteo.com/v1/forecast"
    data = httpx.get(
        weather_url,
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=5,
    ).json()

    current = data["current_weather"]
    return {
        "city": city,
        "temperature": current["temperature"],
        "windspeed": current["windspeed"],
        "weathercode": current["weathercode"],
    }
```

```python
print(get_weather("Seoul"))
# {'city': 'Seoul', 'temperature': 18.5, 'windspeed': 7.2, 'weathercode': 2}
```

---

### Step 2. 상태 정의

> **Copilot 프롬프트**
> ```
> agent.py 파일을 시작해줘.
> LangGraph용 WeatherState를 TypedDict로 정의해줘.
> 필드는 city(str), weather(dict), summary(str), is_ok(bool), attempt(int).
> 각 필드에 한 줄 주석으로 무엇을 담는지 설명해줘.
> ```

```python
# agent.py
from typing import TypedDict

class WeatherState(TypedDict):
    city: str           # 입력: 도시 이름
    weather: dict       # 날씨 API 응답
    summary: str        # LLM이 만든 한 문장 요약
    is_ok: bool         # 검증 통과 여부
    attempt: int        # 요약 시도 횟수
```

---

### Step 3. 노드 작성

> **Copilot 프롬프트**
> ```
> WeatherState를 받는 LangGraph 노드 세 개를 작성해줘.
> - fetch_weather: weather_tool의 get_weather를 호출해서 weather 필드를 반환
> - summarize: weather 데이터를 보고 LLM으로 한 문장 한국어 요약 생성, attempt+1 반환.
>   weather에 error 키가 있으면 그 메시지를 summary로 반환.
> - check: summary가 도시명과 날씨 정보를 포함하는지 LLM에게 yes/no로 판정, is_ok 반환.
> LLM은 ChatGroq(model="llama-3.3-70b-versatile") 사용.
> 각 노드에 print로 진행 상황 출력.
> ```

```python
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from weather_tool import get_weather

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile")

def fetch_weather(state: WeatherState) -> dict:
    result = get_weather(state["city"])
    print(f"[날씨 조회] {result}")
    return {"weather": result}

def summarize(state: WeatherState) -> dict:
    w = state["weather"]
    if "error" in w:
        return {"summary": w["error"], "attempt": state["attempt"] + 1}
    prompt = (
        f"{w['city']}의 현재 날씨: 기온 {w['temperature']}°C, "
        f"풍속 {w['windspeed']}km/h. 비전공자에게 한 문장으로 요약해라."
    )
    result = llm.invoke(prompt)
    print(f"[요약 시도 {state['attempt'] + 1}] {result.content}")
    return {"summary": result.content, "attempt": state["attempt"] + 1}

def check(state: WeatherState) -> dict:
    prompt = (
        f"다음 요약이 도시명과 날씨 정보를 모두 포함하는가? '{state['summary']}'\n"
        "포함하면 'yes', 아니면 'no'만 답해라."
    )
    result = llm.invoke(prompt)
    verdict = result.content.strip().lower() == "yes"
    print(f"[검증] {'통과' if verdict else '재요약 필요'}")
    return {"is_ok": verdict}
```

---

### Step 4. 분기와 그래프 조립

> **Copilot 프롬프트**
> ```
> LangGraph StateGraph로 위 노드들을 연결해줘.
> 흐름: fetch_weather → summarize → check → route 분기.
> route: is_ok True이거나 attempt >= 3이면 END, 아니면 summarize로 재시도.
> graph.compile()까지 작성해줘.
> ```

```python
from langgraph.graph import StateGraph, END

def route(state: WeatherState) -> str:
    if state["is_ok"]:
        return "end"
    if state["attempt"] >= 3:
        print("[종료] 최대 시도 횟수 초과")
        return "end"
    return "summarize"

builder = StateGraph(WeatherState)
builder.add_node("fetch_weather", fetch_weather)
builder.add_node("summarize", summarize)
builder.add_node("check", check)

builder.set_entry_point("fetch_weather")
builder.add_edge("fetch_weather", "summarize")
builder.add_edge("summarize", "check")
builder.add_conditional_edges("check", route, {"end": END, "summarize": "summarize"})

graph = builder.compile()
```

---

### Step 5. 실행

> **Copilot 프롬프트**
> ```
> city="Seoul"로 초기 상태를 만들고 graph.invoke()로 실행하는 코드 작성해줘.
> 최종 summary와 총 attempt 횟수를 출력해줘.
> ```

```python
result = graph.invoke({
    "city": "Seoul",
    "weather": {},
    "summary": "",
    "is_ok": False,
    "attempt": 0,
})

print("\n--- 최종 요약 ---")
print(result["summary"])
print(f"총 시도 횟수: {result['attempt']}")
```

다른 도시("Busan", "Tokyo", "Paris")로도 실행해본다.

---

### Step 6. 실패 케이스 확인

> **Copilot 프롬프트**
> ```
> 존재하지 않는 도시명을 넣었을 때 에러가 어떻게 처리되는지 확인하는 실행 코드 작성해줘.
> ```

존재하지 않는 도시를 입력해서 오류가 숨겨지지 않고 드러나는지 확인한다.

```python
result = graph.invoke({
    "city": "Nonexistentcity123",
    "weather": {},
    "summary": "",
    "is_ok": False,
    "attempt": 0,
})
print(result["summary"])
```

---

## 제출물

- `weather_tool.py`, `agent.py` 전체 코드
- 정상 도시 2개 실행 결과 캡처
- 존재하지 않는 도시 실행 결과 캡처
- 코드 상단 또는 `README.md`에 한 문장 프로젝트 설명

---

## 평가 기준

| 항목 | 내용 |
|------|------|
| 통합 여부 | 날씨 도구와 LangGraph가 실제로 연결되어 작동하는가 |
| 상태 설계 | 상태 필드가 흐름을 반영하는가 |
| 분기와 종료 | 무한 루프 없이 종료되는가 |
| 도구 설명 | `get_weather` docstring이 언제 쓰는지 설명하는가 |
| 실패 처리 | 잘못된 도시명 입력 시 오류가 드러나는가 |
| 설명 가능성 | 코드만 보고 무엇을 하는지 알 수 있는가 |

---

## 다음 주 예고

8주차부터는 RAG 기초와 문서 기반 질의응답으로 넘어간다.
