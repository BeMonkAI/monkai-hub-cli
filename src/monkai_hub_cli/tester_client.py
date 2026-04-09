# -*- coding: utf-8 -*-
"""HTTP client for the MonkAI Tester Railway server."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .config import TESTER_API_KEY, TESTER_API_URL


def execute_test(
    test_id: str,
    execution_id: str,
    interactions: List[Dict[str, Any]],
    dev_config: Dict[str, Any],
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """Call the monkai-tester Railway server to execute a test.

    Args:
        test_id: UUID of the agent_test
        execution_id: UUID of the agent_test_execution
        interactions: List of interaction dicts matching the server schema
        dev_config: Dict with apiUrl, headers, bodyTemplate
        timeout: Request timeout in seconds

    Returns:
        Dict with success, results, kpi_report
    """
    payload = {
        "testId": test_id,
        "executionId": execution_id,
        "interactions": interactions,
        "devConfig": dev_config,
    }

    resp = httpx.post(
        f"{TESTER_API_URL}/api/v1/execute-test",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TESTER_API_KEY}",
        },
        timeout=timeout,
    )

    if resp.status_code != 200:
        detail = ""
        try:
            body = resp.json()
            detail = body.get("detail") or body.get("error") or ""
        except Exception:
            detail = resp.text[:200]
        raise Exception(f"Tester API error ({resp.status_code}): {detail}")

    return resp.json()
