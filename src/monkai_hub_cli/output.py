# -*- coding: utf-8 -*-
"""JSON output helpers for the MonkAI Hub CLI."""

from __future__ import annotations

import json
from typing import Any, Optional


def format_success(**kwargs: Any) -> str:
    data = {"status": "ok", **kwargs}
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_error(message: str, code: Optional[str] = None, **kwargs: Any) -> str:
    data: dict[str, Any] = {"status": "error"}
    if code:
        data["code"] = code
    data["message"] = message
    data.update(kwargs)
    return json.dumps(data, ensure_ascii=False, indent=2)


def print_success(**kwargs: Any) -> None:
    print(format_success(**kwargs))


def print_error(message: str, code: Optional[str] = None, **kwargs: Any) -> None:
    print(format_error(message, code=code, **kwargs))
    raise SystemExit(1)
