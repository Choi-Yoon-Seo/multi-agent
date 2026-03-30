from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode_message(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def read_message(stream, timeout_sec: float = 30.0) -> dict[str, Any]:
    start = time.time()
    header = b""
    while b"\r\n\r\n" not in header:
        if time.time() - start > timeout_sec:
            raise TimeoutError("MCP header read timeout")
        chunk = stream.read(1)
        if not chunk:
            raise RuntimeError("MCP stream closed while reading header")
        header += chunk

    header_text = header.decode("ascii", errors="replace")
    content_length = None
    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    if content_length is None:
        raise ValueError(f"Missing Content-Length header: {header_text!r}")

    body = stream.read(content_length)
    if len(body) != content_length:
        raise RuntimeError("Incomplete MCP body")
    return json.loads(body.decode("utf-8"))


def request(proc: subprocess.Popen, msg: dict[str, Any], wait_id: int, bucket: list[dict[str, Any]]) -> dict[str, Any]:
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(encode_message(msg))
    proc.stdin.flush()

    while True:
        incoming = read_message(proc.stdout, timeout_sec=45.0)
        bucket.append(incoming)
        if incoming.get("id") == wait_id:
            return incoming


def main() -> int:
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.wikipedia.org/"
    screenshot_path_arg = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("practice/chapter3/data/output/playwright-home.png")
    )

    base = Path(__file__).resolve().parents[1]
    out_dir = base / "data" / "output"
    log_dir = base / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    transcript: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "executed_at": now_iso(),
        "server": "@playwright/mcp",
        "status": "started",
        "steps": [],
    }

    proc = subprocess.Popen(
        [
            "npx",
            "-y",
            "@playwright/mcp@latest",
            "--headless",
            "--output-mode",
            "stdout",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )

    try:
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "week3-practice-client", "version": "1.0.0"},
            },
        }
        init_res = request(proc, init_req, wait_id=1, bucket=transcript)
        result["steps"].append({"step": "initialize", "ok": "result" in init_res})

        initialized_noti = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        assert proc.stdin is not None
        proc.stdin.write(encode_message(initialized_noti))
        proc.stdin.flush()
        result["steps"].append({"step": "notifications/initialized", "ok": True})

        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        tools_res = request(proc, tools_req, wait_id=2, bucket=transcript)
        tools = tools_res.get("result", {}).get("tools", [])
        tool_names = [t.get("name") for t in tools if isinstance(t, dict)]
        result["steps"].append({
            "step": "tools/list",
            "ok": True,
            "tool_count": len(tool_names),
            "sample_tools": tool_names[:8],
        })

        selected = None
        for candidate in ["browser_navigate", "browser_snapshot", "browser_take_screenshot", "browser_close"]:
            if candidate in tool_names:
                selected = candidate
                break

        if selected:
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": selected,
                    "arguments": (
                        {"url": target_url}
                        if selected == "browser_navigate"
                        else (
                            {"path": str(screenshot_path_arg)}
                            if selected == "browser_take_screenshot"
                            else {}
                        )
                    ),
                },
            }
            call_res = request(proc, call_req, wait_id=3, bucket=transcript)
            result["steps"].append({
                "step": f"tools/call:{selected}",
                "ok": "result" in call_res,
                "has_error": "error" in call_res,
            })

            # Try a follow-up screenshot if navigate was called and screenshot tool exists.
            if selected == "browser_navigate" and "browser_take_screenshot" in tool_names:
                ss_req = {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "browser_take_screenshot",
                        "arguments": {"path": str(screenshot_path_arg)},
                    },
                }
                ss_res = request(proc, ss_req, wait_id=4, bucket=transcript)
                result["steps"].append({
                    "step": "tools/call:browser_take_screenshot",
                    "ok": "result" in ss_res,
                    "has_error": "error" in ss_res,
                    "path": str(screenshot_path_arg),
                })
        else:
            result["steps"].append({"step": "tools/call", "ok": False, "reason": "candidate tool not found"})

        result["status"] = "success"

    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"

    finally:
        try:
            proc.kill()
        except Exception:
            pass

    stderr_text = ""
    try:
        if proc.stderr is not None:
            stderr_text = proc.stderr.read().decode("utf-8", errors="replace").strip()
    except Exception:
        stderr_text = ""
    if stderr_text:
        result["stderr_tail"] = stderr_text[-2000:]

    result["transcript_size"] = len(transcript)
    result["target_url"] = target_url
    result["screenshot_path"] = str(screenshot_path_arg)

    transcript_path = out_dir / "practice1_playwright_mcp_transcript.json"
    result_path = out_dir / "practice1_tool_calls.json"
    log_path = log_dir / "practice1_run.log"

    transcript_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    log_lines = [
        f"[{now_iso()}] practice1 playwright mcp real start",
        f"status: {result.get('status')}",
        f"steps: {json.dumps(result.get('steps', []), ensure_ascii=False)}",
        f"result_file: {result_path}",
        f"transcript_file: {transcript_path}",
        f"[{now_iso()}] practice1 playwright mcp real done",
    ]
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print(result_path)
    print(transcript_path)
    print(log_path)
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
