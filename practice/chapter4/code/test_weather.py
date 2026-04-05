#!/usr/bin/env python3
"""
Week 4 실습: 날씨 서버 테스트 스크립트

MCP 서버를 띄우지 않고 핵심 로직(fetch_weather, parse_weather_response)만 확인한다.

실행:
    cd practice/chapter4
    source venv/bin/activate
    python code/test_weather.py
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# 같은 폴더의 weather_server 임포트
sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
from weather_server import fetch_weather, parse_weather_response


# ── 테스트 1: parse_weather_response ────────────────────────

class TestParseWeatherResponse(unittest.TestCase):
    """응답 정리 함수 단독 테스트 (API 호출 없음)"""

    SAMPLE_RAW = {
        "name": "Seoul",
        "sys": {"country": "KR"},
        "weather": [{"description": "맑음"}],
        "main": {"temp": 22.3, "feels_like": 21.0, "humidity": 55},
        "wind": {"speed": 3.1},
    }

    def test_normal_response(self):
        result = parse_weather_response(self.SAMPLE_RAW)
        self.assertEqual(result["도시"], "Seoul")
        self.assertEqual(result["습도"], "55%")
        self.assertIn("22.3", result["온도"])

    def test_error_passthrough(self):
        """에러 dict는 그대로 통과해야 한다"""
        error = {"error": "도시를 찾을 수 없습니다: xyz"}
        result = parse_weather_response(error)
        self.assertIn("error", result)

    def test_missing_fields(self):
        """필드가 빠진 응답도 깨지지 않아야 한다"""
        result = parse_weather_response({"name": "Test"})
        self.assertEqual(result["도시"], "Test")
        self.assertIn("?", result["온도"])


# ── 테스트 2: fetch_weather 입력 검증 ────────────────────────

class TestFetchWeatherValidation(unittest.TestCase):
    """fetch_weather의 에러 분기 테스트 (실제 API 호출을 mock)"""

    @patch("weather_server.os.getenv", return_value=None)
    def test_missing_api_key(self, _mock):
        """API 키가 없으면 ValueError"""
        with self.assertRaises(ValueError):
            fetch_weather("Seoul")

    @patch("weather_server.requests.get")
    @patch("weather_server.os.getenv", return_value="fake-key")
    def test_city_not_found_404(self, _env, mock_get):
        """404 응답 → 도시 못 찾음 에러"""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = fetch_weather("InvalidCity")
        self.assertIn("error", result)
        self.assertIn("찾을 수 없습니다", result["error"])

    @patch("weather_server.requests.get")
    @patch("weather_server.os.getenv", return_value="fake-key")
    def test_invalid_key_401(self, _env, mock_get):
        """401 응답 → 인증 실패 에러"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        result = fetch_weather("Seoul")
        self.assertIn("error", result)
        self.assertIn("API 키", result["error"])

    @patch("weather_server.requests.get", side_effect=__import__("requests").exceptions.Timeout)
    @patch("weather_server.os.getenv", return_value="fake-key")
    def test_timeout(self, _env, _mock_get):
        """타임아웃 → 재시도 후 에러"""
        result = fetch_weather("Seoul")
        self.assertIn("error", result)
        self.assertIn("시간 초과", result["error"])

    @patch("weather_server.requests.get")
    @patch("weather_server.os.getenv", return_value="fake-key")
    def test_success(self, _env, mock_get):
        """200 응답 → 정상 데이터 반환"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "name": "Seoul",
            "sys": {"country": "KR"},
            "weather": [{"description": "맑음"}],
            "main": {"temp": 20, "feels_like": 19, "humidity": 60},
            "wind": {"speed": 2.5},
        }
        mock_get.return_value = mock_resp

        result = fetch_weather("Seoul")
        self.assertEqual(result["name"], "Seoul")


if __name__ == "__main__":
    print("=" * 50)
    print(" 날씨 서버 핵심 로직 테스트")
    print("=" * 50)
    unittest.main(verbosity=2)
