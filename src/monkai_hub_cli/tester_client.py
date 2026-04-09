# -*- coding: utf-8 -*-
"""HTTP client for test execution via Supabase Edge Function.

The Edge Function `python-test-executor` proxies to the monkai-tester
Railway server internally. The CLI only needs the user's JWT — no
server API keys required.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .auth import get_token
from .config import EDGE_FUNCTION_URL, SUPABASE_ANON_KEY


def execute_test(
    test_id: str,
    execution_id: str,
    interactions: List[Dict[str, Any]],
    dev_config: Dict[str, Any],
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """Execute a test via the Supabase Edge Function.

    The Edge Function authenticates the user via JWT, verifies test
    ownership, and proxies the request to the monkai-tester Railway
    server (which has the API key configured server-side).

    Args:
        test_id: UUID of the agent_test
        execution_id: UUID of the agent_test_execution
        interactions: List of interaction dicts matching the server schema
        dev_config: Dict with apiUrl, headers, bodyTemplate
        timeout: Request timeout in seconds

    Returns:
        Dict with success, results, kpi_report
    """
    token = get_token()

    payload = {
        "testId": test_id,
        "executionId": execution_id,
        "interactions": interactions,
        "devConfig": dev_config,
    }

    resp = httpx.post(
        EDGE_FUNCTION_URL,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
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
        raise Exception(f"Test execution failed ({resp.status_code}): {detail}")

    return resp.json()
