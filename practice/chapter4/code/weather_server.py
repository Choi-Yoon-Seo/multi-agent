#!/usr/bin/env python3
"""
Week 4 실습: OpenWeatherMap API를 MCP 서버로 래핑

구조:
    fetch_weather(city)          — HTTP 요청만 담당
    parse_weather_response(data) — 응답 JSON에서 필요한 필드만 추출
    get_weather(city)            — MCP 도구로 노출

실행:
    cd practice/chapter4
    source venv/bin/activate
    python code/weather_server.py --demo          # API 직접 테스트
    python code/weather_server.py                 # MCP 서버 모드
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── 경로 설정 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = CHAPTER_DIR / "data" / "output"
LOG_DIR = CHAPTER_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── 환경 변수 ──────────────────────────────────────────────
load_dotenv(CHAPTER_DIR / ".env")

# ── 로깅 ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "weather.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── 상수 ──────────────────────────────────────────────────
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT = 10  # 초
MAX_RETRIES = 2


# ============================================================
# 1) API 호출 함수
# ============================================================

def fetch_weather(city: str) -> dict:
    """
    도시 이름으로 OpenWeatherMap 현재 날씨를 조회한다.

    - timeout=10
    - 일시적 서버 오류(5xx)만 최대 2회 재시도
    - 실패 시 명확한 에러 dict 반환
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "kr",
    }

    logger.info("weather request started: city=%s", city)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()
            response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
            elapsed = time.time() - start

            # 성공
            if response.status_code == 200:
                logger.info(
                    "weather request succeeded: city=%s elapsed=%.2fs",
                    city, elapsed,
                )
                return response.json()

            # 404 — 도시 못 찾음 (재시도 불필요)
            if response.status_code == 404:
                logger.warning("weather request failed: city=%s reason=not_found", city)
                return {"error": f"도시를 찾을 수 없습니다: {city}"}

            # 401 — 인증 실패 (재시도 불필요)
            if response.status_code == 401:
                logger.warning("weather request failed: city=%s reason=invalid_key", city)
                return {"error": "API 키가 유효하지 않습니다"}

            # 5xx — 서버 오류 (재시도)
            last_error = f"서버 오류 (HTTP {response.status_code})"
            logger.warning(
                "weather request failed: city=%s attempt=%d reason=%s",
                city, attempt, last_error,
            )

        except requests.exceptions.Timeout:
            last_error = "서버 응답 시간 초과"
            logger.warning(
                "weather request failed: city=%s attempt=%d reason=timeout",
                city, attempt,
            )

        except requests.exceptions.ConnectionError:
            last_error = "네트워크 연결 실패"
            logger.warning(
                "weather request failed: city=%s attempt=%d reason=connection_error",
                city, attempt,
            )

        # 재시도 전 잠깐 대기
        if attempt < MAX_RETRIES:
            time.sleep(1)

    return {"error": f"요청 실패 ({MAX_RETRIES}회 재시도 후): {last_error}"}


# ============================================================
# 2) 응답 정리 함수
# ============================================================

def parse_weather_response(data: dict) -> dict:
    """
    OpenWeatherMap 원시 응답에서 온도·습도·날씨 상태만 뽑아
    사람이 읽기 쉬운 dict로 반환한다.
    """
    if "error" in data:
        return data

    return {
        "도시": data.get("name", "알 수 없음"),
        "국가": data.get("sys", {}).get("country", ""),
        "날씨": data.get("weather", [{}])[0].get("description", "알 수 없음"),
        "온도": f'{data.get("main", {}).get("temp", "?")}°C',
        "체감온도": f'{data.get("main", {}).get("feels_like", "?")}°C',
        "습도": f'{data.get("main", {}).get("humidity", "?")}%',
        "풍속": f'{data.get("wind", {}).get("speed", "?")} m/s',
    }


# ============================================================
# 3) MCP 도구 연결
# ============================================================

mcp = FastMCP("weather-server")


@mcp.tool()
def get_weather(city: str) -> str:
    """
    도시 이름을 입력하면 현재 날씨를 알려줍니다.
    예: get_weather("Seoul"), get_weather("Tokyo")
    """
    city = city.strip()
    if not city:
        return json.dumps({"error": "도시 이름을 입력해주세요."}, ensure_ascii=False)

    raw = fetch_weather(city)
    result = parse_weather_response(raw)

    # 결과를 output 폴더에 저장
    output = {
        "result": result,
        "queried_at": datetime.now(timezone.utc).isoformat(),
    }
    output_file = OUTPUT_DIR / "weather_result.json"
    output_file.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("결과 저장: %s", output_file)

    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 데모 실행
# ============================================================

def demo():
    """MCP 서버 없이 핵심 로직만 직접 테스트"""
    print("=" * 50)
    print(" OpenWeatherMap 데모 실행")
    print("=" * 50)

    test_cities = ["Seoul", "InvalidCityName12345"]

    for city in test_cities:
        print(f"\n--- {city} ---")
        raw = fetch_weather(city)
        result = parse_weather_response(raw)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print("MCP 서버 시작... (stdio 모드)")
        print("데모 실행: python weather_server.py --demo")
        mcp.run(transport="stdio")
