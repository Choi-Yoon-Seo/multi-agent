#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_files(relative_path: str = ".", max_items: int = 20) -> dict[str, Any]:
    target = (ROOT / relative_path).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return {"ok": False, "error": "허용된 프로젝트 경로 밖 접근은 금지됩니다."}
    if not target.exists() or not target.is_dir():
        return {"ok": False, "error": "존재하지 않는 디렉토리입니다."}
    items = sorted([p.name for p in target.iterdir()])[:max_items]
    return {
        "ok": True,
        "path": str(target.relative_to(ROOT)),
        "items": items,
        "count": len(items),
    }


def handle(msg: dict[str, Any]) -> dict[str, Any]:
    method = msg.get("method")
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "list_project_files",
                        "description": "읽기 전용으로 프로젝트 디렉토리 목록을 반환합니다.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "relative_path": {"type": "string", "default": "."},
                                "max_items": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                            },
                            "additionalProperties": False,
                        },
                    }
                ]
            },
            "meta": {"generated_at": now_iso()},
        }

    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        if name != "list_project_files":
            return {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": -32601, "message": "지원하지 않는 도구입니다."},
            }
        if not isinstance(args, dict):
            return {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": -32602, "message": "arguments는 객체여야 합니다."},
            }
        rel = args.get("relative_path", ".")
        max_items = args.get("max_items", 20)
        if not isinstance(rel, str) or not isinstance(max_items, int):
            return {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": -32602, "message": "relative_path는 문자열, max_items는 정수여야 합니다."},
            }
        result = list_files(rel, max_items)
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id"),
            "result": result,
            "meta": {"generated_at": now_iso()},
        }

    return {
        "jsonrpc": "2.0",
        "id": msg.get("id"),
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
