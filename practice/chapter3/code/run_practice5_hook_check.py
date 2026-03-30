from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    output_dir = base / "data" / "output"
    log_dir = base / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    file_count = sum(1 for p in output_dir.rglob("*") if p.is_file())
    status = "pass" if file_count >= 1 else "fail"

    result = {
        "executed_at": now_iso(),
        "event": "Stop",
        "checked_path": str(output_dir),
        "file_count": file_count,
        "status": status,
    }

    result_path = output_dir / "practice5_hook_check.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = log_dir / "practice5_hook_check.log"
    log_path.write_text(
        f"[{now_iso()}] hook-check status={status} file_count={file_count}\n",
        encoding="utf-8",
    )

    print(result_path)
    print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
