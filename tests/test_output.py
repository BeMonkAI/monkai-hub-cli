# -*- coding: utf-8 -*-
"""Tests for output helpers."""

import json

from monkai_hub_cli.output import format_error, format_success


def test_format_success():
    result = format_success(test_id="abc", name="test1")
    parsed = json.loads(result)
    assert parsed["status"] == "ok"
    assert parsed["test_id"] == "abc"


def test_format_error_with_code():
    result = format_error("failed", code="AUTH_ERROR")
    parsed = json.loads(result)
    assert parsed["status"] == "error"
    assert parsed["code"] == "AUTH_ERROR"


def test_format_error_without_code():
    result = format_error("generic")
    parsed = json.loads(result)
    assert parsed["status"] == "error"
    assert "code" not in parsed
