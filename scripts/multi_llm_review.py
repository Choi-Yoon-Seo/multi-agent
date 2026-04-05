from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional

# python-dotenv 사용
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv가 없으면 수동으로 로드
    def load_env_file():
        """프로젝트 루트의 .env 파일을 로드한다"""
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
    load_env_file()


PROJECT_PROMPT = """당신은 대중 기술 교재의 사실성 검증자이다.
이 교재는 학술논문이 아니므로, 학술적 엄격함보다는 내용의 정확성과 최신성을 검토한다.

검토 규칙 (3가지 핵심):

1. **작성된 내용이 거짓이 아니고 사실인가?**
   - 기술적 설명, 명령어, API 사용법이 실제로 작동하는 내용인가?
   - 가짜 실행 결과, 임의로 만든 수치, 존재하지 않는 도구/라이브러리를 언급하지 않았는가?
   - 플랫폼 종속 경로나 명령어를 하드코딩하여 다른 환경에서 실행 불가능하게 만들지 않았는가?
   → 거짓이나 오류가 있으면 critical로 지적한다.

2. **내용이 최신 내용인가?**
   - 언급된 도구, 라이브러리, Python 버전이 현재(2026년 1월 기준) 표준과 맞는가?
   - 더 이상 사용되지 않는(deprecated) 방법이나 오래된 버전을 권장하지 않는가?
   - 최신 모범 사례(best practices)를 반영하고 있는가?
   → 구식이거나 비권장 방식이면 major로 지적한다.

3. **참고문헌이 사실인가?**
   - 참고문헌의 URL, DOI, 문서 제목이 실제로 존재하고 접근 가능한가?
   - 공식 문서 링크가 올바른가? (예: Python 공식 문서, 라이브러리 공식 페이지)
   - 허구의 논문이나 존재하지 않는 링크를 인용하지 않았는가?
   → 거짓 참고문헌이 있으면 critical로 지적한다.

추가 검토 사항 (교재 품질):
- 본문에 3~5줄을 넘는 코드 블록이 있으면 minor로 지적한다.
- 실습 코드 참조 형식(_전체 코드는 practice/chapter{N}/code/{파일명}.py 참고_)이 누락되면 minor로 지적한다.

출력은 반드시 JSON 하나만 반환하라(마크다운 금지). JSON 스키마:
{
  "summary": "요약 3~5문장",
  "critical_issues": [{"title": "...", "detail": "...", "location_hint": "..."}],
  "major_issues": [{"title": "...", "detail": "...", "location_hint": "..."}],
  "minor_suggestions": [{"title": "...", "detail": "...", "location_hint": "..."}]
}
"""


@dataclass
class ProviderResult:
    provider: str
    model: str
    ok: bool
    error: Optional[str]
    review: Optional[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="다중 LLM으로 챕터 원고를 검토합니다.")
    parser.add_argument("--chapter", type=int, required=True, help="챕터 번호 (예: 3)")
    parser.add_argument(
        "--openai-model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI 모델명 (기본값: OPENAI_MODEL 또는 gpt-4o)",
    )
    parser.add_argument(
        "--anthropic-model",
        default=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        help="Anthropic 모델명 (기본값: CLAUDE_MODEL 또는 claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--grok-model",
        default=os.getenv("GROK_MODEL", "grok-4-1-fast-reasoning"),
        help="Grok 모델명 (기본값: GROK_MODEL 또는 grok-4-1-fast-reasoning)",
    )
    parser.add_argument(
        "--output-dir",
        default="content/reviews",
        help="리뷰 JSON 출력 디렉토리(프로젝트 루트 기준 상대 경로)",
    )
    return parser.parse_args()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_chapter_markdown(chapter: int) -> tuple[Path, str]:
    root = project_root()
    md_path = root / "docs" / f"ch{chapter}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"원고 파일을 찾을 수 없습니다: {md_path}")
    return md_path, md_path.read_text(encoding="utf-8")


def safe_json_loads(text: str, provider: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{provider} 응답이 JSON이 아닙니다: {e}") from e


def review_with_openai(model: str, manuscript: str) -> ProviderResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ProviderResult(provider="openai", model=model, ok=False, error="OPENAI_API_KEY not set", review=None)

    try:
        from openai import OpenAI
    except Exception as e:
        return ProviderResult(provider="openai", model=model, ok=False, error=f"openai import failed: {e}", review=None)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROJECT_PROMPT},
                {"role": "user", "content": manuscript},
            ],
            temperature=0.2,
            timeout=120.0  # 2분 타임아웃
        )
        content = response.choices[0].message.content or ""
        review = safe_json_loads(content, "openai")
        return ProviderResult(provider="openai", model=model, ok=True, error=None, review=review)
    except Exception as e:
        return ProviderResult(provider="openai", model=model, ok=False, error=str(e), review=None)


def review_with_anthropic(model: str, manuscript: str) -> ProviderResult:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ProviderResult(
            provider="anthropic", model=model, ok=False, error="ANTHROPIC_API_KEY not set", review=None
        )

    try:
        import anthropic
    except Exception as e:
        return ProviderResult(
            provider="anthropic", model=model, ok=False, error=f"anthropic import failed: {e}", review=None
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=4096,  # 더 긴 응답 허용
            temperature=0.2,
            timeout=120.0,  # 2분 타임아웃
            system=PROJECT_PROMPT,
            messages=[{"role": "user", "content": manuscript}],
        )
        text = ""
        for block in message.content:
            if getattr(block, "type", None) == "text":
                text += block.text
        review = safe_json_loads(text, "anthropic")
        return ProviderResult(provider="anthropic", model=model, ok=True, error=None, review=review)
    except Exception as e:
        return ProviderResult(provider="anthropic", model=model, ok=False, error=str(e), review=None)


def review_with_grok(model: str, manuscript: str) -> ProviderResult:
    api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    if not api_key:
        return ProviderResult(
            provider="grok", model=model, ok=False, error="GROK_API_KEY or XAI_API_KEY not set", review=None
        )

    try:
        from openai import OpenAI
    except Exception as e:
        return ProviderResult(provider="grok", model=model, ok=False, error=f"openai import failed: {e}", review=None)

    try:
        # Grok은 OpenAI 호환 API 사용
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROJECT_PROMPT},
                {"role": "user", "content": manuscript},
            ],
            temperature=0.2,
            timeout=120.0  # 2분 타임아웃
        )
        content = response.choices[0].message.content or ""
        review = safe_json_loads(content, "grok")
        return ProviderResult(provider="grok", model=model, ok=True, error=None, review=review)
    except Exception as e:
        return ProviderResult(provider="grok", model=model, ok=False, error=str(e), review=None)


def write_review_file(chapter: int, output_dir: Path, payload: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"ch{chapter}_review_{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    args = parse_args()
    md_path, manuscript = read_chapter_markdown(args.chapter)

    results = [
        review_with_openai(args.openai_model, manuscript),
        review_with_anthropic(args.anthropic_model, manuscript),
        review_with_grok(args.grok_model, manuscript),
    ]

    payload: dict[str, Any] = {
        "chapter": args.chapter,
        "input_path": md_path.as_posix(),
        "generated_on": date.today().isoformat(),
        "providers": [asdict(r) for r in results],
    }

    ok_results = [r for r in results if r.ok and r.review is not None]
    if not ok_results:
        payload["skipped"] = True
        payload["skip_reason"] = "No provider produced a review (missing API keys and/or network restrictions)."

    out_path = write_review_file(args.chapter, project_root() / args.output_dir, payload)
    print(out_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
