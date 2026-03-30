from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def call_server(requests: list[dict]) -> list[dict]:
    server = Path(__file__).resolve().parent / "minimal_mcp_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(server)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    responses = []
    for req in requests:
        proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline().strip()
        responses.append(json.loads(line))

    proc.stdin.close()
    proc.wait(timeout=5)
    return responses


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    out = base / "data" / "output"
    logs = base / "logs"
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "list_project_files",
                "arguments": {"relative_path": "practice", "max_items": 5},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_project_files",
                "arguments": {"relative_path": "../../", "max_items": 5},
            },
        },
    ]

    responses = call_server(reqs)
    out_json = {
        "executed_at": now_iso(),
        "requests": reqs,
        "responses": responses,
    }

    result_path = out / "practice3_mcp_test_results.json"
    result_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = logs / "practice3_mcp_test.log"
    log_path.write_text(
        "\n".join([
            f"[{now_iso()}] practice3 test start",
            f"requests: {len(reqs)}",
            f"result: {result_path}",
            f"[{now_iso()}] practice3 test done",
        ]) + "\n",
        encoding="utf-8",
    )

    print(result_path)
    print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
