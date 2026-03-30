#!/usr/bin/env python3
"""memo_mcp_server.py 통합 테스트.

테스트 시나리오:
  1. tools/list  → 도구 3개(save_memo, list_memos, read_memo) 확인
  2. save_memo   → 메모 저장 성공
  3. list_memos  → 저장한 메모가 목록에 존재
  4. read_memo   → 저장한 메모 본문 확인
  5. read_memo   → 존재하지 않는 파일 → 오류
  6. save_memo   → 빈 제목 → 오류
  7. read_memo   → 경로 조작(../) → 오류

실행:
  macOS  : python3 practice/chapter3/code/test_memo_mcp_server.py
  Windows: py -3   practice/chapter3/code/test_memo_mcp_server.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT_DIR = HERE.parent / "data" / "output"
LOG_DIR = HERE.parent / "logs"
MEMO_DIR = HERE.parent / "data" / "memos"
SERVER = HERE / "memo_mcp_server.py"


def send(proc: subprocess.Popen, msg: dict) -> dict:
    """서버 프로세스에 JSON-RPC 요청을 보내고 응답을 받는다."""
    payload = json.dumps(msg, ensure_ascii=False) + "\n"
    proc.stdin.write(payload)
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line)


def run_tests() -> list[dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 테스트 전 메모 디렉토리 초기화
    if MEMO_DIR.exists():
        shutil.rmtree(MEMO_DIR)

    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(ROOT),
    )

    results = []
    saved_filename = None

    try:
        # ── 1) tools/list ────────────────────────────────
        resp = send(proc, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tool_names = [t["name"] for t in resp.get("result", {}).get("tools", [])]
        results.append({
            "test": "tools/list",
            "id": 1,
            "pass": set(tool_names) == {"save_memo", "list_memos", "read_memo"},
            "tool_names": tool_names,
            "response": resp,
        })

        # ── 2) save_memo (정상) ──────────────────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {
                "name": "save_memo",
                "arguments": {
                    "title": "회의록 테스트",
                    "body": "3주차 MCP 실습 회의 내용:\n- 최소 서버 구현 완료\n- 메모 도구 추가 결정",
                },
            },
        })
        ok = resp.get("result", {}).get("ok", False)
        saved_filename = resp.get("result", {}).get("filename")
        results.append({
            "test": "save_memo (정상)",
            "id": 2,
            "pass": ok is True and saved_filename is not None,
            "response": resp,
        })

        # ── 3) list_memos ────────────────────────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "list_memos", "arguments": {}},
        })
        memos = resp.get("result", {}).get("memos", [])
        found = any(m["filename"] == saved_filename for m in memos)
        results.append({
            "test": "list_memos",
            "id": 3,
            "pass": found and resp.get("result", {}).get("count", 0) >= 1,
            "response": resp,
        })

        # ── 4) read_memo (정상) ──────────────────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "read_memo", "arguments": {"filename": saved_filename}},
        })
        content = resp.get("result", {}).get("content", "")
        results.append({
            "test": "read_memo (정상)",
            "id": 4,
            "pass": "회의록 테스트" in content and "MCP 실습" in content,
            "response": resp,
        })

        # ── 5) read_memo (존재하지 않는 파일) ────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "read_memo", "arguments": {"filename": "nonexistent.md"}},
        })
        results.append({
            "test": "read_memo (존재하지 않는 파일)",
            "id": 5,
            "pass": resp.get("result", {}).get("ok") is False,
            "response": resp,
        })

        # ── 6) save_memo (빈 제목) ───────────────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "save_memo", "arguments": {"title": "", "body": "내용"}},
        })
        results.append({
            "test": "save_memo (빈 제목 → 오류)",
            "id": 6,
            "pass": resp.get("result", {}).get("ok") is False,
            "response": resp,
        })

        # ── 7) read_memo (경로 조작) ─────────────────────
        resp = send(proc, {
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": "read_memo", "arguments": {"filename": "../../../etc/passwd"}},
        })
        results.append({
            "test": "read_memo (경로 조작 차단)",
            "id": 7,
            "pass": resp.get("result", {}).get("ok") is False,
            "response": resp,
        })

    finally:
        proc.stdin.close()
        proc.wait(timeout=5)

    return results


def main() -> int:
    ts = datetime.now(timezone.utc).isoformat()
    results = run_tests()

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    # 결과 JSON 저장
    output = {
        "server": "memo_mcp_server.py",
        "executed_at": ts,
        "summary": f"{passed}/{total} passed",
        "results": results,
    }
    out_path = OUTPUT_DIR / "practice3_memo_mcp_test_results.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # 로그 저장
    log_lines = [
        f"[{ts}] memo_mcp_server 테스트 실행",
        f"[{ts}] 결과: {passed}/{total} passed",
    ]
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        log_lines.append(f"  [{status}] {r['test']}")
    log_path = LOG_DIR / "practice3_memo_mcp_test.log"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    # 콘솔 출력
    print(f"\n{'='*50}")
    print(f"memo_mcp_server 테스트 결과: {passed}/{total} passed")
    print(f"{'='*50}")
    for r in results:
        mark = "✓" if r["pass"] else "✗"
        print(f"  {mark} {r['test']}")
    print(f"\n결과 JSON: {out_path.relative_to(ROOT)}")
    print(f"로그: {log_path.relative_to(ROOT)}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
