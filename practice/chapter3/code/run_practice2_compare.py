from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import shorten
from datetime import datetime, timezone


@dataclass
class SummaryResult:
    mode: str
    output_file: str
    has_verification: bool
    has_uncertainty_marker: bool
    verification_items: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def naive_summary(text: str) -> str:
    return shorten(text.replace("\n", " "), width=110, placeholder="...")


def ruled_summary(text: str) -> str:
    summary = shorten(text.replace("\n", " "), width=150, placeholder="...")
    checks = [
        "요약이 원문 핵심 개념(MCP/Skill/Plugin 분리)을 포함하는지 확인",
        "출력 경로가 practice/chapter3/data/output/인지 확인",
        "불확실 정보는 '확인 필요'로 표기했는지 확인",
    ]
    lines = [
        "# Summary (With Rules)",
        "",
        "## 요약",
        summary,
        "",
        "## 검증 항목",
    ]
    lines.extend([f"- {c}" for c in checks])
    lines.extend(["", "## 불확실 정보", "- 확인 필요: 외부 MCP 서버 실연결(Copilot/CLI) 여부는 로컬 명령으로 재확인 필요"])
    return "\n".join(lines) + "\n"


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    docs = base / "docs"
    out = base / "data" / "output"
    logs = base / "logs"
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    text = (docs / "notes.md").read_text(encoding="utf-8")

    no_rules_path = out / "summary_no_rules.md"
    no_rules_text = "# Summary (No Rules)\n\n" + naive_summary(text) + "\n"
    no_rules_path.write_text(no_rules_text, encoding="utf-8")

    with_rules_path = out / "summary_with_rules.md"
    with_rules_path.write_text(ruled_summary(text), encoding="utf-8")

    result = {
        "executed_at": utc_now(),
        "source": str(docs / "notes.md"),
        "results": [
            asdict(SummaryResult(
                mode="no_rules",
                output_file=str(no_rules_path),
                has_verification=False,
                has_uncertainty_marker=False,
                verification_items=[],
            )),
            asdict(SummaryResult(
                mode="with_rules",
                output_file=str(with_rules_path),
                has_verification=True,
                has_uncertainty_marker=True,
                verification_items=[
                    "핵심 개념 포함 확인",
                    "출력 경로 확인",
                    "불확실 표기 확인",
                ],
            )),
        ],
    }

    result_path = out / "practice2_comparison.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = logs / "practice2_run.log"
    log_path.write_text(
        "\n".join([
            f"[{utc_now()}] practice2 start",
            f"wrote: {no_rules_path}",
            f"wrote: {with_rules_path}",
            f"wrote: {result_path}",
            f"[{utc_now()}] practice2 done",
        ]) + "\n",
        encoding="utf-8",
    )

    print(no_rules_path)
    print(with_rules_path)
    print(result_path)
    print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
