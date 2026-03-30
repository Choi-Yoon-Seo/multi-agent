# Week 4. 첫 MCP 서버 만들기: 외부 API 래핑과 A2A 개요

> 원본: docs/ch4.md

## 학습 목표

- 외부 API를 MCP 서버로 래핑할 때 고려할 사항(인증/실패/로깅/테스트)을 설명한다
- OAuth 2.1 기반 원격 MCP 서버 인증의 흐름과 핵심 개념을 이해한다
- A2A(Agent-to-Agent) 프로토콜의 개념과 MCP와의 관계를 설명한다
- MCP, A2A, 직접 API 호출 중 상황에 맞는 프로토콜을 선택할 수 있다

---

## 선수 지식

- 3장에서 다룬 MCP 도구(tool) 설계 원칙과 명세 작성 방법을 이해하고 있어야 한다
- Python 기본 문법과 비동기 프로그래밍(async/await)에 대한 기초 지식이 있으면 따라오기 수월하다

---

## 기초 용어 정리

이 장에서 자주 등장하는 핵심 용어들을 먼저 정리합니다.

### API (Application Programming Interface)

- **쉽게 말하면**: 프로그램끼리 대화하는 방법
- **예시**: 날씨 정보를 제공하는 서버에 "서울 날씨 알려줘"라고 요청하면 JSON 형식으로 데이터를 받는 것
- **웹 API**: 인터넷을 통해 특정 주소(URL)로 요청을 보내면 데이터를 받을 수 있는 서비스
  - 예: `https://api.openweathermap.org/data/2.5/weather?q=Seoul`

### 래핑(Wrapping)

- **정의**: 기존의 복잡한 기능을 더 쉽고 안전하게 사용할 수 있도록 감싸는 것
- **비유**: 
  - 날카로운 칼을 그대로 쓰면 위험하지만, 안전 손잡이를 씌우면 편하게 쓸 수 있다
  - 복잡한 외부 API를 그대로 쓰면 에러 처리가 어렵지만, MCP 서버로 감싸면 에이전트가 안전하게 쓸 수 있다
- **구체적으로**:
  ```
  외부 API (복잡, 에러 많음) 
    ↓ 래핑 (감싸기)
  MCP 서버 (단순, 안전, 표준화된 인터페이스)
    ↓
  AI 에이전트 (편하게 사용)
  ```

### MCP 서버 vs MCP 도구

- **MCP 서버**: AI 에이전트가 외부 세계와 소통할 수 있게 해주는 프로그램 (전체 시스템)
- **MCP 도구(tool)**: MCP 서버가 제공하는 개별 기능
  - 예: 날씨 MCP 서버 → `get_current_weather` 도구, `get_forecast` 도구

### 인증(Authentication)

- **정의**: "너는 누구니?"를 확인하는 과정
- **왜 필요한가**: 아무나 API를 무제한 사용하면 서버가 과부하될 수 있고, 비용이 발생할 수 있다
- **방법**:
  - **API 키**: 고유한 문자열 (예: `abcd1234efgh5678`)
  - 요청할 때 이 키를 함께 보내면 "나는 등록된 사용자입니다"를 증명

### 비동기 프로그래밍 (async/await)

- **동기 방식**: 일을 순서대로 하나씩 끝내고 다음으로 넘어감
  ```python
  result1 = 작업1()  # 끝날 때까지 기다림
  result2 = 작업2()  # 작업1이 끝나야 시작
  ```
- **비동기 방식**: 기다리는 동안 다른 일을 할 수 있음
  ```python
  result1 = await 작업1()  # 기다리는 동안 다른 일 가능
  result2 = await 작업2()
  ```
- **언제 필요한가**: 네트워크 요청처럼 응답을 기다리는 시간이 긴 작업에서 효율적

### 환경 변수 (Environment Variable)

- **정의**: 프로그램이 실행되는 컴퓨터에 저장된 설정 값
- **왜 사용하는가**: 
  - API 키 같은 민감한 정보를 코드에 직접 쓰면 위험 (Git에 올리면 노출)
  - 개발/운영 환경에서 다른 값을 쓸 수 있음
- **사용 예**:
  ```
  # .env 파일
  OPENWEATHERMAP_API_KEY=abc123
  ```
  ```python
  # Python 코드
  api_key = os.getenv("OPENWEATHERMAP_API_KEY")
  ```

---

## 4.1 외부 API 래핑의 목표와 고려사항

### 왜 직접 API를 호출하지 않고 래핑하는가?

AI 에이전트가 외부 API를 직접 호출하면 발생하는 문제들:

1. **표준화되지 않은 인터페이스**: 각 API마다 다른 방식으로 요청/응답
2. **에러 처리의 어려움**: 네트워크 오류, 인증 실패 등을 매번 다르게 처리
3. **보안 위험**: API 키를 에이전트에 직접 노출
4. **재사용 어려움**: 같은 API를 여러 에이전트에서 쓸 때 중복 코드 발생

MCP 서버로 래핑하면:
- ✅ 모든 도구가 같은 형식(MCP 프로토콜)을 따름
- ✅ 에러를 서버에서 일관되게 처리
- ✅ API 키를 서버에만 저장, 에이전트는 모름
- ✅ 한 번 만들면 어디서든 재사용 가능

### 외부 API를 사용할 때 발생하는 불확실성

외부 API는 우리가 통제할 수 없는 영역입니다. 다음과 같은 문제가 언제든 발생할 수 있습니다:

- ❌ 네트워크가 갑자기 끊김
- ❌ API 서버가 과부하로 응답이 느림
- ❌ 인증 토큰이 만료됨
- ❌ 요청이 너무 많아서 제한(rate limit)에 걸림
- ❌ API 응답 형식이 예상과 다름

⚠️ **중요**: 이런 불확실성을 MCP 서버 내부에서 처리하지 않으면, 에이전트는 예측할 수 없는 실패를 경험하고 제대로 동작하지 않습니다.

**표 4.1** 외부 API 호출 시 문제 유형과 대응 전략

| 문제 유형 | 원인 | 대응 전략 | 설명 |
|----------|------|----------|------|
| 네트워크 오류 | 연결 실패, DNS 오류 | 재시도(지수 백오프) | 잠시 후 다시 시도하되, 대기 시간을 점점 늘림 |
| 인증 실패 | 잘못된 키, 만료된 키 | 명확한 에러 메시지, 키 검증 | 사용자가 키를 확인하고 수정할 수 있도록 안내 |
| 레이트 리밋 | 요청 과다 | 대기 후 재시도, 캐싱 | 요청 횟수 제한에 걸렸을 때 잠시 기다림 |
| 응답 지연 | 서버 과부하 | 타임아웃 설정, 취소 | 너무 오래 기다리지 않고 일정 시간 후 포기 |
| 잘못된 응답 | API 스키마 변경 | 응답 검증, 폴백 처리 | 예상과 다른 형식이면 기본값 사용 |

### 실습 예제: OpenWeatherMap API

이 장에서는 실제로 동작하는 날씨 정보 MCP 서버를 만들어봅니다.

**OpenWeatherMap API를 선택한 이유**:
- ✅ 무료 티어를 제공 (하루 1,000회 요청까지 무료)
- ✅ API 키 발급이 간단 (이메일만 있으면 5분 안에 가능)
- ✅ 요청/응답 구조가 명확하고 문서화가 잘 되어 있음
- ✅ 날씨 정보는 실시간 데이터이므로 실행할 때마다 다른 결과를 확인 가능

**API 호출 예시**:
```bash
# 서울 날씨 조회
curl "https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid=YOUR_API_KEY"
```

**응답 예시** (JSON):
```json
{
  "weather": [{"main": "Clear", "description": "clear sky"}],
  "main": {"temp": 298.15, "humidity": 60},
  "name": "Seoul"
}
```

이 API를 MCP 서버로 래핑하면:
- 에이전트는 복잡한 URL이나 API 키를 몰라도 됨
- `get_current_weather(city="Seoul")` 같은 간단한 함수 호출로 날씨 정보를 얻음
- 네트워크 오류나 잘못된 도시명 등의 에러를 서버가 처리

---

## 4.2 인증키 관리: .env와 환경 변수

### ❌ 잘못된 방법: API 키를 코드에 직접 쓰기

```python
# 절대 이렇게 하지 마세요!
api_key = "abcd1234efgh5678ijkl"  # ⚠️ 위험!
url = f"https://api.openweathermap.org/data/2.5/weather?appid={api_key}"
```

**왜 위험한가?**

1. **Git 저장소에 올리면 즉시 노출**
   - 공개 저장소라면 전 세계에 공개됨
   - 비공개 저장소라도 팀원 모두가 볼 수 있음
   - 나중에 저장소가 공개되거나 유출되면 키가 노출됨

2. **로그에 기록되면 위험**
   - 요청 URL 전체를 로그에 남기면 쿼리 파라미터의 키도 함께 기록됨
   - 로그 파일이 다른 시스템으로 전송되면 노출 범위가 더 넓어짐

3. **키를 변경하기 어려움**
   - 키가 유출되면 여러 파일을 모두 수정해야 함

### ✅ 올바른 방법: 환경 변수 사용

**단계 1: `.env` 파일 만들기**

프로젝트 루트 디렉토리에 `.env` 파일을 만들고 API 키를 저장합니다:

```bash
# .env 파일
OPENWEATHERMAP_API_KEY=abcd1234efgh5678ijkl
```

**단계 2: `.gitignore`에 추가하기**

`.env` 파일이 Git에 올라가지 않도록 보호합니다:

```bash
# .gitignore 파일
.env
*.env
!.env.example
```

**단계 3: `.env.example` 파일 만들기**

팀원들과 어떤 환경 변수가 필요한지 공유합니다 (실제 키는 포함하지 않음):

```bash
# .env.example 파일 (Git에 올려도 안전)
OPENWEATHERMAP_API_KEY=your_api_key_here
```

**단계 4: Python 코드에서 사용하기**

```python
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 읽기
api_key = os.getenv("OPENWEATHERMAP_API_KEY")

# 키가 없으면 에러 메시지 출력
if not api_key:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

# 이제 안전하게 사용 가능
url = f"https://api.openweathermap.org/data/2.5/weather?appid={api_key}"
```

_전체 코드는 [practice/chapter4/code/4-6-weather-mcp-server.py](practice/chapter4/code/4-6-weather-mcp-server.py) 참고_

### 환경 변수 우선순위

`python-dotenv`는 다음 순서로 환경 변수를 찾습니다:

1. **시스템 환경 변수** (터미널에서 `export`로 설정한 것)
2. `.env` 파일의 변수

**예시**:
```bash
# 터미널에서
export OPENWEATHERMAP_API_KEY=system_key

# Python에서 load_dotenv() 실행 후
# os.getenv("OPENWEATHERMAP_API_KEY") → "system_key"
# (.env 파일의 값은 무시됨)
```

**왜 이렇게 설계되었나?**
- 개발 환경: `.env` 파일 사용
- 운영 환경: 시스템 환경 변수로 설정 (서버 관리자만 접근 가능)
- 운영 환경에는 `.env` 파일을 배포하지 않아도 됨

### 실습 체크리스트

- [ ] `.env` 파일 생성 및 API 키 저장
- [ ] `.gitignore`에 `.env` 추가 확인
- [ ] `.env.example` 파일 생성
- [ ] `python-dotenv` 패키지 설치 (`pip install python-dotenv`)
- [ ] 코드에서 `load_dotenv()` 호출 및 환경 변수 읽기 테스트

---

## 4.3 실패 처리: 타임아웃, 재시도, 에러 응답

### 왜 실패 처리가 중요한가?

외부 API는 언제든 실패할 수 있습니다. 성공하는 경우만 생각하고 코드를 짜면, 실패했을 때 프로그램이 멈추거나 예상치 못한 동작을 하게 됩니다.

**꼭 처리해야 할 세 가지**:
1. ⏱️ **타임아웃**: 너무 오래 기다리지 않기
2. 🔄 **재시도**: 일시적 오류는 다시 시도하기
3. 📝 **에러 응답**: 실패 원인을 명확히 전달하기

---

### 1️⃣ 타임아웃 설정: 무한 대기 방지

**문제 상황**: API 서버가 응답하지 않으면?

```python
# ❌ 타임아웃 없음 → 무한 대기 가능
response = requests.get(url)  # 서버가 응답 안 하면 영원히 기다림
```

**해결 방법**: 타임아웃 설정

```python
# ✅ 10초 후에는 포기
response = requests.get(url, timeout=10)
```

**타임아웃 시간 선택 가이드**:
- 빠른 API (데이터베이스 조회): 1~5초
- 일반 웹 API: 10~30초
- 무거운 계산/파일 다운로드: 60초 이상

**실제 사용 예시**:
```python
import httpx

async def fetch_weather(city: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://api.openweathermap.org/...")
            return response.json()
    except httpx.TimeoutException:
        return {"error": "요청 시간 초과 (10초). 네트워크를 확인하세요."}
```

---

### 2️⃣ 재시도 전략: 언제 다시 시도할까?

**재시도하면 안 되는 경우** (즉시 실패 반환):

| HTTP 상태 코드 | 의미 | 재시도 여부 | 이유 |
|--------------|------|-----------|------|
| 400 | 잘못된 요청 | ❌ | 요청 자체가 잘못됨. 다시 보내도 같은 오류 |
| 401 | 인증 실패 | ❌ | API 키가 틀림. 키를 수정해야 함 |
| 404 | 찾을 수 없음 | ❌ | 잘못된 URL이나 도시명 |

**재시도해야 하는 경우**:

| HTTP 상태 코드 | 의미 | 재시도 여부 | 이유 |
|--------------|------|-----------|------|
| 500 | 서버 오류 | ✅ | 일시적 장애일 수 있음 |
| 502, 503 | 서버 과부하 | ✅ | 잠시 후 복구될 수 있음 |
| 네트워크 오류 | 연결 끊김 | ✅ | 일시적 네트워크 문제 |

---

### 3️⃣ 지수 백오프: 점점 느리게 재시도하기

**지수 백오프(Exponential Backoff)란?**

재시도할 때 대기 시간을 지수적으로 늘리는 전략입니다.

**왜 필요한가?**
- 서버가 과부하 상태라면 즉시 재시도하면 상황을 악화시킴
- 조금씩 기다리면서 재시도해야 서버가 복구될 시간을 줌

**작동 방식**:
```
첫 번째 시도: 즉시 실패 → 1초 대기
두 번째 시도: 실패 → 2초 대기 (2^1)
세 번째 시도: 실패 → 4초 대기 (2^2)
네 번째 시도: 실패 → 8초 대기 (2^3)
최종 포기
```

**구현 예시**:
```python
import time

max_retries = 3

for attempt in range(max_retries):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()  # 성공!
        
        # 4xx 오류는 재시도 안 함
        if 400 <= response.status_code < 500:
            return {"error": f"요청 오류: {response.status_code}"}
        
        # 5xx 오류는 재시도
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1, 2, 4초
            print(f"재시도 {attempt + 1}/{max_retries}, {wait_time}초 대기...")
            time.sleep(wait_time)
    
    except requests.Timeout:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            print(f"타임아웃. {wait_time}초 후 재시도...")
            time.sleep(wait_time)

return {"error": "최대 재시도 횟수 초과"}
```

_전체 코드는 [practice/chapter4/code/4-6-weather-mcp-server.py](practice/chapter4/code/4-6-weather-mcp-server.py) 참고_

---

### 4️⃣ 명확한 에러 응답 형식

**❌ 나쁜 예**: 예외만 발생시키기
```python
def get_weather(city):
    if not api_key:
        raise Exception("키 없음")  # 에이전트가 처리하기 어려움
```

**✅ 좋은 예**: 구조화된 JSON 응답
```python
def get_weather(city):
    if not api_key:
        return {
            "success": False,
            "error": "API 키가 설정되지 않았습니다. .env 파일을 확인하세요.",
            "error_code": "MISSING_API_KEY"
        }
```

**왜 더 좋은가?**
- 에이전트가 `success` 필드로 성공/실패를 쉽게 판단
- `error` 메시지로 사용자에게 무엇을 해야 하는지 안내 가능
- `error_code`로 프로그래밍적으로 에러 처리 가능

**다양한 에러 케이스**:
```python
# 인증 실패
{"success": False, "error": "API 키가 유효하지 않습니다", "error_code": "INVALID_API_KEY"}

# 잘못된 도시명
{"success": False, "error": "도시를 찾을 수 없습니다: Seoulll", "error_code": "CITY_NOT_FOUND"}

# 네트워크 오류
{"success": False, "error": "네트워크 연결 실패. 인터넷을 확인하세요", "error_code": "NETWORK_ERROR"}

# 타임아웃
{"success": False, "error": "요청 시간 초과 (10초)", "error_code": "TIMEOUT"}
```

---

---

## 4.4 로깅: 요청과 응답을 추적 가능하게

### 로깅이란?

프로그램이 실행되는 동안 일어나는 일들을 기록하는 것입니다.

**비유**: 프로그램의 "일기"를 쓰는 것
- 언제 무슨 일이 일어났는지 기록
- 문제가 생겼을 때 과거로 돌아가서 원인 파악 가능

### 왜 로깅이 필수인가?

**시나리오**: 운영 중인 MCP 서버에서 갑자기 오류 발생

❌ **로깅 없으면?**
- 사용자: "서울 날씨 안 나와요"
- 개발자: "음... 언제요? 어떤 오류였나요?"
- 사용자: "아까요. 그냥 안 됐어요"
- 개발자: "😓 원인을 모르겠네요..."

✅ **로깅 있으면?**
- 사용자: "서울 날씨 안 나와요"
- 개발자: 로그 확인 → "아, 2026-03-30 14:23에 API 키 만료 오류네요. 바로 수정하겠습니다"

### Python logging 모듈 기본 사용법

**로그 레벨 (심각도 순서)**:

| 레벨 | 용도 | 예시 |
|------|------|------|
| **DEBUG** | 상세한 디버깅 정보 | "요청 파라미터: city=Seoul, units=metric" |
| **INFO** | 일반 정보 | "API 호출 성공: 서울 날씨 조회" |
| **WARNING** | 경고 (프로그램은 계속 실행) | "API 응답이 느립니다 (3초 소요)" |
| **ERROR** | 오류 발생 | "API 호출 실패: 인증 오류" |
| **CRITICAL** | 치명적 오류 | "서버 시작 실패: 포트 이미 사용 중" |

**기본 설정**:
```python
import logging

# 로그 설정
logging.basicConfig(
    filename="logs/mcp_server.log",  # 로그 파일 경로
    level=logging.INFO,  # INFO 이상만 기록 (DEBUG는 제외)
    format="%(asctime)s - %(levelname)s - %(message)s"
    # 출력 형식: 2026-03-30 14:23:45 - INFO - API 호출 성공
)

# 로그 기록
logging.info("MCP 서버 시작")
logging.warning("API 키가 곧 만료됩니다")
logging.error("날씨 조회 실패: 네트워크 오류")
```

**로그 파일 예시** (`logs/mcp_server.log`):
```
2026-03-30 14:23:45 - INFO - MCP 서버 시작
2026-03-30 14:24:12 - INFO - API 호출 성공: city=Seoul
2026-03-30 14:25:33 - ERROR - API 호출 실패: 타임아웃
2026-03-30 14:25:35 - INFO - 재시도 1/3
2026-03-30 14:25:37 - INFO - API 호출 성공: city=Seoul
```

_전체 코드는 [practice/chapter4/code/4-6-weather-mcp-server.py](practice/chapter4/code/4-6-weather-mcp-server.py) 참고_

---

### ⚠️ 주의사항 1: 민감 정보 마스킹

**절대 로그에 기록하면 안 되는 것**:
- API 키
- 비밀번호
- 사용자 개인정보 (주민번호, 신용카드 번호 등)
- 인증 토큰

**❌ 나쁜 예**:
```python
logging.info(f"API 호출: https://api.weather.com?key=abcd1234efgh5678")
# 로그 파일에 API 키가 그대로 노출!
```

**✅ 좋은 예**:
```python
def mask_api_key(url: str) -> str:
    """API 키를 마스킹"""
    # abcd1234efgh5678 → abcd...5678
    import re
    def mask(match):
        key = match.group(1)
        return f"key={key[:4]}...{key[-4:]}"
    return re.sub(r'key=([a-zA-Z0-9]+)', mask, url)

masked_url = mask_api_key(url)
logging.info(f"API 호출: {masked_url}")
# 로그: https://api.weather.com?key=abcd...5678  ✅ 안전
```

**실제 사건**: 한 개발팀의 교훈

- **문제**: 디버깅용으로 요청 URL 전체를 로그에 기록
- **결과**: 쿼리 파라미터의 API 키가 로그 파일에 노출
- **확산**: 로그가 모니터링 시스템으로 자동 전송되면서 더 많은 사람에게 노출
- **교훈**: 
  - 민감 정보는 반드시 마스킹
  - URL 대신 엔드포인트와 파라미터를 분리해서 기록
  - API 키는 아예 로그에서 제외

---

### ⚠️ 주의사항 2: MCP 서버에서 print() 사용 금지!

**MCP 서버에서 절대 하면 안 되는 것**:
```python
print("날씨 조회 중...")  # ❌ MCP 통신을 깨뜨림!
```

**왜 안 되나?**

MCP 프로토콜은 **표준 출력(stdout)**을 사용해서 통신합니다:
```
클라이언트 ←─ JSON 메시지 (stdout) ─→ MCP 서버
```

`print()`를 쓰면:
```
클라이언트 ←─ "날씨 조회 중..." + JSON 메시지 ─→ MCP 서버
                ↑ 이 부분 때문에 JSON 파싱 실패!
```

**✅ 올바른 방법**: `logging` 모듈 사용

`logging`은 **표준 에러(stderr)**로 출력되므로 안전합니다:
```python
import logging

logging.info("날씨 조회 중...")  # ✅ stderr로 출력, 통신 안전
```

**요약**:
- ❌ `print()`: stdout (MCP 통신 방해)
- ✅ `logging`: stderr (안전)

---

### 로깅 모범 사례

**1. 의미 있는 정보만 기록하기**
```python
# ❌ 너무 애매
logging.info("성공")

# ✅ 구체적
logging.info("날씨 조회 성공: city=Seoul, temp=15.3°C")
```

**2. 에러 발생 시 컨텍스트 포함**
```python
# ❌ 정보 부족
logging.error("실패")

# ✅ 디버깅 가능
logging.error(f"API 호출 실패: city={city}, status_code={status}, error={error}")
```

**3. 로그 레벨 적절히 사용**
```python
logging.debug(f"요청 파라미터: {params}")  # 개발 중에만 필요
logging.info("API 호출 성공")  # 정상 동작 기록
logging.warning("응답 시간 3초 초과")  # 주의 필요
logging.error("타임아웃 발생")  # 오류 발생
```

**4. 개발 vs 운영 환경**
```python
import os

# 개발 환경: 상세 로그 (DEBUG)
# 운영 환경: 필수 로그만 (INFO)
log_level = logging.DEBUG if os.getenv("ENV") == "dev" else logging.INFO

logging.basicConfig(level=log_level)
```

---

---

## 4.5 테스트 가능한 구조: 의존성 분리

### 외부 API에 의존하는 코드의 테스트 문제

**시나리오**: 날씨 API를 호출하는 함수를 테스트하려고 합니다.

```python
def get_weather(city: str):
    # 실제 API 호출
    response = requests.get(f"https://api.openweathermap.org/...")
    return response.json()
```

**테스트 시 문제점**:
1. ❌ API 서버가 다운되면 테스트 실패
2. ❌ 테스트할 때마다 실제 비용 발생 가능
3. ❌ 너무 많은 테스트로 rate limit 초과
4. ❌ 테스트가 느림 (네트워크 대기 시간)
5. ❌ 인터넷 없으면 테스트 불가능

### 해결책: 모킹(Mocking)

**모킹이란?**
- 실제 외부 시스템을 **가짜로 대체**하는 테스트 기법
- 비유: 실제 은행 시스템 대신 "모형 은행"으로 테스트하는 것

**예시**:
```python
# 실제 코드
def get_weather(city: str):
    response = requests.get(f"https://api.openweathermap.org/...")
    return response.json()

# 테스트 코드
def test_get_weather():
    # 가짜 응답 만들기
    fake_response = {
        "weather": [{"main": "Clear"}],
        "main": {"temp": 298.15}
    }
    
    # requests.get을 가짜로 대체
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = fake_response
        
        # 이제 실제 API 호출 없이 테스트 가능!
        result = get_weather("Seoul")
        assert result["weather"][0]["main"] == "Clear"
```

### 의존성 주입: 테스트 가능한 설계

**❌ 나쁜 설계**: 의존성이 내부에 숨겨짐
```python
def get_weather(city: str):
    # API 클라이언트를 내부에서 생성 → 테스트하기 어려움
    client = WeatherAPIClient()
    return client.fetch(city)
```

**✅ 좋은 설계**: 의존성을 외부에서 주입
```python
def get_weather(city: str, client=None):
    # 기본값은 실제 클라이언트
    if client is None:
        client = WeatherAPIClient()
    
    # client를 외부에서 제공받을 수 있음
    return client.fetch(city)

# 실제 사용
result = get_weather("Seoul")  # 실제 API 호출

# 테스트 사용
fake_client = FakeWeatherAPIClient()
result = get_weather("Seoul", client=fake_client)  # 가짜 사용
```

### 실습 코드의 구조

실습 코드는 `WeatherAPIClient` 클래스로 API 로직을 분리했습니다:

```python
class WeatherAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def fetch_weather(self, city: str) -> dict:
        # 실제 API 호출
        url = f"https://api.openweathermap.org/...&appid={self.api_key}"
        response = httpx.get(url)
        return response.json()

# 테스트용 가짜 클라이언트
class FakeWeatherAPIClient:
    def fetch_weather(self, city: str) -> dict:
        # API 호출 없이 가짜 데이터 반환
        return {
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "main": {"temp": 298.15, "humidity": 60},
            "name": city
        }
```

**테스트 결과**:

| 테스트 항목 | 테스트 수 | 통과 | 실패 |
|------------|---------|------|------|
| API 키 마스킹 | 3 | 3 | 0 |
| 날씨 데이터 파싱 | 3 | 3 | 0 |
| 입력 검증 | 4 | 4 | 0 |
| **합계** | **10** | **10** | **0** |

_테스트 결과는 `practice/chapter4/data/output/ch04_test_results.json`에 저장_

### 의존성 주입의 장점

1. **테스트 가능**: 가짜 객체로 대체 가능
2. **유연성**: 다른 구현체로 쉽게 교체
3. **격리**: 각 부분을 독립적으로 테스트
4. **빠른 테스트**: 네트워크 호출 없이 즉시 실행

---

## 4.6 OAuth 2.1 인증: 원격 MCP 서버의 인증 프레임워크

### 배경

4.2절에서는 **로컬 환경**에서 `.env` 파일로 API 키를 관리하는 방법을 배웠습니다.

하지만 **원격 MCP 서버**를 운영하려면:
- 여러 클라이언트(사용자)가 접속
- 각 클라이언트를 인증해야 함
- API 키 방식은 한계가 있음 (키 공유, 권한 관리 어려움)

**해결책**: OAuth 2.1 표준 인증 프레임워크 사용

### OAuth 2.1이란? (간단 버전)

**비유**: 호텔 키 카드

1. **프론트 데스크**(인가 서버): 신분증 확인 후 키 카드 발급
2. **키 카드**(액세스 토큰): 객실 출입 권한
3. **객실 도어**(MCP 서버): 키 카드 확인 후 입실 허용

**흐름**:
```
사용자 → 인가 서버 (로그인) → 토큰 받음
        ↓
사용자 → MCP 서버 (토큰 제시) → 서비스 이용
```

### MCP에서 OAuth 2.1 도입 연혁 (참고)

**2025년 3월**: 첫 도입
- MCP 서버가 인증도 직접 처리
- 간단하지만 대규모 조직에서 비효율적

**2025년 6월**: 개선
- 인증 서버와 MCP 서버 분리
- 조직의 기존 인증 시스템(Okta, Azure AD) 활용 가능

**2025년 11월**: 보안 강화
- PKCE 필수 적용 (코드 탈취 공격 방지)

### 실무에서 언제 사용하나?

| 환경 | 인증 방식 |
|------|----------|
| 로컬 개발 | `.env` 파일 (4.2절) |
| 팀 내부 서버 | API 키 + 간단한 인증 |
| 공개 서비스 | **OAuth 2.1** (필수) |

**이번 장에서는 기초만 다룹니다**. OAuth 2.1의 자세한 구현은 고급 과정에서 다룹니다.
  - CIMD(Client ID Metadata Document, 클라이언트 등록을 간소화하는 문서 형식)가 도입되었다

### 인증 흐름 요약

- 원격 MCP 서버의 OAuth 2.1 인증 흐름 (단계별)
  1. MCP 클라이언트가 서버에 접속하면, 서버는 Protected Resource Metadata(RFC 9728)로 인가 서버 정보를 제공한다
  2. 클라이언트는 인가 서버에 PKCE를 포함한 인가 요청을 보낸다
  3. 사용자가 브라우저에서 인증하고 권한을 부여한다
  4. 클라이언트는 인가 코드와 PKCE 검증자를 교환하여 액세스 토큰을 받는다
  5. 클라이언트는 이 토큰으로 MCP 서버에 요청한다

- 실습과의 관계
  - 이 장의 실습에서는 로컬 STDIO 방식을 사용하므로 OAuth 인증이 필요하지 않다
  - ⚠ 프로덕션 환경에서 원격 MCP 서버를 배포할 때는 OAuth 2.1 인증을 반드시 구현해야 한다

---

## 4.7 A2A(Agent-to-Agent) 프로토콜 개요

- MCP와 A2A의 역할 구분
  - MCP: "에이전트와 도구 간" 통신을 표준화한다
  - A2A: "에이전트와 에이전트 간" 통신을 표준화한다

- A2A 프로토콜 소개
  - Google이 2025년 4월에 발표했다
  - 같은 해 6월 Linux Foundation에 이관했다
  - 목적: 서로 다른 프레임워크로 만들어진 에이전트들이 상호 운용할 수 있는 표준을 제공한다
  - 2026년 3월 기준으로 다수의 기술 기업과 플랫폼 벤더가 참여하고 있지만, 참여 조직 수는 발표 시점마다 달라지므로 공식 프로젝트 페이지를 확인하는 것이 안전하다

### A2A의 핵심 개념

- Agent Card (능력 광고)
  - A2A 서버는 `/.well-known/agent-card.json` 경로에 JSON 메타데이터를 게시한다
  - Agent Card에 포함되는 정보:
    - 에이전트의 이름
    - 설명
    - 지원 기능(스트리밍, 푸시 알림)
    - 인증 요구사항
  - 클라이언트 에이전트는 이 카드를 읽고 상대방의 능력을 파악한 후 작업을 위임할지 결정한다

- Client/Remote 모델
  - 클라이언트 에이전트: 작업을 위임하는 쪽
  - 리모트 에이전트: 작업을 수행하는 쪽
  - MCP의 클라이언트/서버 구조와 유사하다
  - 차이점: A2A에서는 양쪽 모두 자율적인 에이전트라는 점이 다르다

- 태스크 생명주기
  - A2A의 태스크는 일곱 가지 상태를 가진다:
    - `submitted`: 접수
    - `working`: 처리 중
    - `input-required`: 추가 입력 필요
    - `completed`: 완료
    - `failed`: 실패
    - `canceled`: 취소
    - `unknown`: 미확인
  - MCP의 Tasks primitive(3.2절)와 유사한 비동기 패턴이다

- 멀티모달 Parts (다양한 데이터 형식을 하나의 태스크에서 처리하는 구조)
  - A2A의 메시지와 아티팩트는 Part로 구성된다
  - Part의 세 가지 유형:
    - TextPart: 텍스트
    - FilePart: 파일
    - DataPart: 구조화된 JSON
  - 결과: 텍스트·이미지·파일·구조화 데이터를 하나의 태스크에서 주고받을 수 있다

- 기술 스택
  - JSON-RPC 2.0 over HTTP(S)를 사용한다
  - v0.3(2025년 7월)부터 gRPC도 지원한다

---

## 4.8 프로토콜 선택 기준: MCP vs A2A vs 직접 API 호출

- 에이전트 시스템을 설계할 때 "어떤 프로토콜을 사용할 것인가"는 중요한 의사결정 포인트다

**표 4.3** 프로토콜 선택 가이드

| 기준 | 직접 API 호출 | MCP | A2A |
|------|-------------|-----|-----|
| 통신 대상 | 단일 외부 서비스 | 에이전트 ↔ 도구/데이터 | 에이전트 ↔ 에이전트 |
| 적합한 상황 | 단순 통합, 일회성 호출 | 도구 재사용, 여러 클라이언트 지원 | 이종 에이전트 협업, 멀티벤더 |
| 표준화 수준 | 각 API마다 상이 | JSON-RPC 2.0, 도구/리소스 스키마 | JSON-RPC 2.0, Agent Card, Task |
| 초기 비용 | 낮음 | 중간 (서버 구현) | 높음 (에이전트 인프라) |
| 재사용성 | 낮음 (하드코딩) | 높음 (플랫폼 독립) | 높음 (프레임워크 독립) |

- 직접 API 호출이 적합한 경우
  - 외부 서비스를 한 곳에서만 사용한다
  - 도구를 재사용할 필요가 없다
  - 단순한 요청-응답으로 충분하다
  - → 예시: 특정 스크립트에서 날씨 API를 한 번 호출하는 정도라면 MCP 서버를 만들 필요가 없다

- MCP가 적합한 경우
  - 동일한 도구를 여러 AI 클라이언트(Claude, ChatGPT developer mode, Codex, 커스텀 에이전트)에서 사용한다
  - 도구의 접근 제어와 감사가 중요하다
  - → 예시: 이 장에서 만든 날씨 서버처럼, 한 번 잘 만들어두면 여러 프로젝트에서 재사용할 수 있다

- A2A가 적합한 경우
  - 서로 다른 팀이나 조직이 만든 에이전트들이 협업해야 한다
  - → 예시: 헬프데스크 에이전트가 모니터링 에이전트에게 서버 상태를 확인하고, 배포 에이전트에게 롤백을 요청하는 시나리오

- 실무에서의 MCP + A2A 조합 사용
  - 실무에서는 MCP와 A2A를 함께 사용하는 경우가 많다
  - 구조:
    - MCP로 개별 도구와 데이터 소스에 접근한다
    - A2A로 에이전트 간 작업을 위임한다
  - A2A의 실전 구현은 제7장에서 다룬다

---

## 4.9 실습: OpenWeatherMap API를 MCP 서버로 래핑

- 이 절의 목표
  - 앞서 설명한 원칙들을 적용하여 실제 MCP 서버를 구현한다
  - OpenWeatherMap의 Current Weather API를 래핑한다
  - 위도와 경도를 입력받아 현재 날씨 정보를 반환하는 도구를 만든다

### 환경 설정

- Python 가상환경 생성 및 의존성 설치

```bash
cd practice/chapter4
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

- `.env` 파일 생성 및 API 키 설정
  - API 키는 https://openweathermap.org/api 에서 무료로 발급받을 수 있다

```
OPENWEATHERMAP_API_KEY=your_api_key_here
```

### MCP 서버 구조

- FastMCP를 사용하여 MCP 서버를 구현한다
  - FastMCP의 특징: Python 타입 힌트와 docstring을 분석하여 자동으로 도구 스키마를 생성한다

```python
mcp = FastMCP("weather-server")

@mcp.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """지정된 위치의 현재 날씨를 조회합니다."""
```

_전체 코드는 practice/chapter4/code/4-6-weather-mcp-server.py 참고_

### 핵심 구현 요소

- 인증키 관리
  - `.env` 파일에서 API 키를 로드한다
  - 로그에는 마스킹된 형태로 기록한다

- 입력 검증
  - 위도는 -90~90 범위를 벗어나면 에러를 반환한다
  - 경도는 -180~180 범위를 벗어나면 에러를 반환한다

- 실패 처리
  - 타임아웃: 10초
  - 최대 재시도: 3회
  - 재시도 방식: 지수 백오프 적용

- 로깅
  - 모든 요청과 응답을 `logs/mcp_server.log`에 기록한다

- 응답 구조화
  - 원시 API 응답에서 필요한 정보만 추출한다
  - 일관된 형태로 반환한다

### 테스트 실행

- 테스트 클라이언트를 실행하여 핵심 로직을 검증할 수 있다

```bash
python3 code/4-6-test-client.py
```

- 테스트가 성공하면 `data/output/ch04_test_results.json`에 결과가 저장된다

### 의사결정 포인트

- HTTP 클라이언트 선택: `requests` vs `httpx`
  - MCP 서버는 비동기로 동작하므로 비동기를 기본 지원하는 `httpx`가 더 적합하다
  - ⚠ `requests`도 사용할 수 있지만, 별도의 스레드 풀이 필요해 복잡해진다

- 재시도 횟수와 타임아웃 결정
  - ⚠ 너무 짧으면 일시적 오류에 취약하다
  - ⚠ 너무 길면 사용자 경험이 나빠진다
  - 일반적인 웹 API의 적절한 출발점: 타임아웃 10초, 재시도 3회
  - 실제 운영에서는 API의 특성에 맞게 조정해야 한다

- 에러 메시지 상세도 결정
  - ⚠ 너무 상세하면 내부 구현이 노출될 수 있다
  - ⚠ 너무 간략하면 디버깅이 어렵다
  - 권장 방식: 클라이언트에게는 "인증 실패" 같은 개요만 전달하고, 상세 정보는 서버 로그에 기록한다

---

---

## 핵심 정리

이 장에서 배운 내용을 정리합니다:

### 1. 래핑이란?
외부 API를 MCP 서버로 감싸서 AI 에이전트가 안전하고 편하게 사용할 수 있게 만드는 것

### 2. API 키 관리 (4.2절)
- ❌ 코드에 직접 쓰기 → Git에 올리면 노출
- ✅ `.env` 파일에 저장 → `.gitignore`에 추가
- `.env.example`로 필요한 변수 목록 공유

### 3. 실패 처리 (4.3절)
- **타임아웃**: 10초 같은 제한 시간 설정 (무한 대기 방지)
- **재시도**: 네트워크 오류 등 일시적 문제는 지수 백오프로 재시도
- **에러 응답**: 구조화된 JSON으로 명확한 메시지 전달

### 4. 로깅 (4.4절)
- `logging` 모듈 사용 (콘솔이나 파일에 기록)
- ⚠️ 민감 정보(API 키)는 마스킹
- ⚠️ MCP 서버에서 `print()` 사용 금지 (통신 방해)

### 5. 테스트 가능한 구조 (4.5절)
- **모킹**: 실제 API 호출 없이 가짜 데이터로 테스트
- **의존성 주입**: 함수에 객체를 외부에서 전달받도록 설계

### 6. OAuth 2.1 (4.6절)
- 원격 MCP 서버의 표준 인증 방식
- 로컬 개발은 `.env`로 충분, 공개 서비스는 OAuth 필요

### 이 장이 중요한 이유
단순히 "API를 호출하는 코드"를 만드는 게 아니라, **production에서 실제로 동작하는 안정적인 시스템**을 만드는 방법을 배웠습니다.

---

## 실습 체크리스트

이 장을 완료했는지 확인하세요:

- [ ] 기초 용어 (API, 래핑, 환경 변수 등) 이해
- [ ] `.env` 파일 생성 및 API 키 관리
- [ ] `.gitignore`에 `.env` 추가 확인
- [ ] 타임아웃과 재시도 로직 구현
- [ ] `logging` 모듈로 로그 기록
- [ ] API 키 마스킹 함수 작성
- [ ] 테스트 코드 작성 (모킹 사용)
- [ ] practice/chapter4/code/4-6-weather-mcp-server.py 실행 및 이해

---

## 다음 장 예고

다음 장에서는 이 장에서 만든 MCP 서버를 **LangChain 에이전트와 연결**합니다.

**배울 내용**:
- 에이전트가 여러 MCP 도구 중 하나를 선택하고 호출하는 과정
- 구조화된 출력(Structured Outputs)으로 도구 호출의 신뢰성을 높이는 방법
- OpenAI Agents SDK와의 비교

---

## 참고문헌

Anthropic. (2025). Model Context Protocol - Build Server. https://modelcontextprotocol.io/docs/develop/build-server

Anthropic. (2025). MCP Authorization Specification. https://modelcontextprotocol.io/specification/draft/basic/authorization

Google. (2025). Announcing the Agent2Agent Protocol (A2A). Google Developers Blog. https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

Linux Foundation. (2025). Linux Foundation Launches the Agent2Agent Protocol Project. https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project

A2A Protocol. (2025). A2A Protocol Specification. https://a2a-protocol.org/latest/specification/

OpenWeatherMap. (2025). Current Weather Data API. https://openweathermap.org/current

Python Software Foundation. (2025). logging - Logging facility for Python. https://docs.python.org/3/library/logging.html

theskumar. (2025). python-dotenv. https://github.com/theskumar/python-dotenv
