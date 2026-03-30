#!/usr/bin/env python3
"""프로젝트 메모 관리 최소 MCP 서버.

제공 도구:
  - save_memo   : 제목+본문으로 메모를 저장한다 (쓰기)
  - list_memos  : 저장된 메모 목록을 반환한다 (읽기)
  - read_memo   : 특정 메모의 본문을 반환한다 (읽기)

설계 원칙:
  1. 저장 경로를 프로젝트 내부(practice/chapter3/data/memos/)로 제한한다.
  2. 파일명에 타임스탬프를 붙여 충돌을 방지한다.
  3. 입력 검증(빈 문자열, 타입)을 명확하게 수행한다.
  4. 오류 메시지를 사람이 읽을 수 있는 한국어로 반환한다.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMO_DIR = Path(__file__).resolve().parents[1] / "data" / "memos"

TOOLS = [
    {
        "name": "save_memo",
        "description": "제목과 본문으로 메모를 저장합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "메모 제목 (파일명에 사용)"},
                "body": {"type": "string", "description": "메모 본문"},
            },
            "required": ["title", "body"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_memos",
        "description": "저장된 메모 목록(제목·생성일)을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "read_memo",
        "description": "파일명으로 특정 메모의 본문을 읽어 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "읽을 메모 파일명"},
            },
            "required": ["filename"],
            "additionalProperties": False,
        },
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(title: str) -> str:
    """제목에서 파일명에 안전한 문자열을 만든다."""
    slug = re.sub(r"[^\w가-힣-]", "_", title).strip("_")[:40]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{slug}.md"


# ── 도구 구현 ──────────────────────────────────────────────

def _save_memo(args: dict[str, Any]) -> dict[str, Any]:
    title = args.get("title", "")
    body = args.get("body", "")
    if not isinstance(title, str) or not title.strip():
        return {"ok": False, "error": "title은 비어 있지 않은 문자열이어야 합니다."}
    if not isinstance(body, str) or not body.strip():
        return {"ok": False, "error": "body는 비어 있지 않은 문자열이어야 합니다."}

    MEMO_DIR.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(title)
    content = f"# {title.strip()}\n\n{body.strip()}\n"
    (MEMO_DIR / filename).write_text(content, encoding="utf-8")
    return {"ok": True, "filename": filename, "path": str(MEMO_DIR / filename)}


def _list_memos(_args: dict[str, Any]) -> dict[str, Any]:
    if not MEMO_DIR.exists():
        return {"ok": True, "memos": [], "count": 0}
    memos = []
    for p in sorted(MEMO_DIR.glob("*.md")):
        first_line = p.read_text(encoding="utf-8").split("\n", 1)[0]
        title = first_line.lstrip("# ").strip() if first_line.startswith("#") else p.stem
        memos.append({"filename": p.name, "title": title})
    return {"ok": True, "memos": memos, "count": len(memos)}


def _read_memo(args: dict[str, Any]) -> dict[str, Any]:
    filename = args.get("filename", "")
    if not isinstance(filename, str) or not filename.strip():
        return {"ok": False, "error": "filename은 비어 있지 않은 문자열이어야 합니다."}
    # 경로 조작 방지
    if "/" in filename or "\\" in filename or ".." in filename:
        return {"ok": False, "error": "파일명에 경로 구분자를 포함할 수 없습니다."}
    target = MEMO_DIR / filename
    if not target.exists():
        return {"ok": False, "error": f"메모를 찾을 수 없습니다: {filename}"}
    return {"ok": True, "filename": filename, "content": target.read_text(encoding="utf-8")}


HANDLERS = {
    "save_memo": _save_memo,
    "list_memos": _list_memos,
    "read_memo": _read_memo,
}


# ── JSON-RPC 라우터 ────────────────────────────────────────

def handle(msg: dict[str, Any]) -> dict[str, Any]:
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS},
            "meta": {"generated_at": now_iso()},
        }

    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})

        fn = HANDLERS.get(name)  # type: ignore[arg-type]
        if fn is None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"지원하지 않는 도구입니다: {name}"},
            }
        if not isinstance(args, dict):
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32602, "message": "arguments는 객체여야 합니다."},
            }
        result = fn(args)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
            "meta": {"generated_at": now_iso()},
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": "지원하지 않는 method입니다."},
    }


def main() -> int:
    import sys
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            response = handle(msg)
        except json.JSONDecodeError:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "JSON 파싱 실패"},
            }
        print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
