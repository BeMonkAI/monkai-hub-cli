# -*- coding: utf-8 -*-
"""Supabase REST API client for MonkAI Hub tables."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from .auth import get_token, get_user_id
from .config import SUPABASE_ANON_KEY, SUPABASE_URL


def _headers() -> Dict[str, str]:
    token = get_token()
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


# ---------------------------------------------------------------------------
# agent_tests
# ---------------------------------------------------------------------------


def list_tests() -> List[Dict[str, Any]]:
    """List all tests for the authenticated user."""
    resp = httpx.get(
        _rest_url("agent_tests"),
        headers=_headers(),
        params={"select": "*", "order": "created_at.desc"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def get_test(test_id: str) -> Dict[str, Any]:
    """Get a single test by ID."""
    resp = httpx.get(
        _rest_url("agent_tests"),
        headers=_headers(),
        params={"select": "*", "id": f"eq.{test_id}"},
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise Exception(f"Test {test_id} not found")
    return data[0]


def create_test(
    name: str,
    test_type: str = "service",
    description: str = "",
    api_url: str = "",
    headers: Optional[Dict[str, str]] = None,
    data_template: Optional[Dict[str, Any]] = None,
    agent_name: str = "",
    repeat_count: int = 1,
) -> Dict[str, Any]:
    """Create a new agent test."""
    user_id = get_user_id()
    payload = {
        "user_id": user_id,
        "name": name,
        "description": description,
        "test_type": test_type,
        "status": "draft",
        "api_url": api_url,
        "headers": headers or {},
        "data_template": data_template or {},
        "agent_name": agent_name,
        "repeat_count": repeat_count,
    }
    resp = httpx.post(
        _rest_url("agent_tests"),
        headers=_headers(),
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()[0]


# ---------------------------------------------------------------------------
# agent_test_interactions
# ---------------------------------------------------------------------------


def get_interactions(test_id: str) -> List[Dict[str, Any]]:
    """Get all interactions for a test, ordered by interaction_number."""
    resp = httpx.get(
        _rest_url("agent_test_interactions"),
        headers=_headers(),
        params={
            "select": "*",
            "test_id": f"eq.{test_id}",
            "order": "interaction_number.asc",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def add_interaction(
    test_id: str,
    interaction_number: int,
    user_message: str,
    first_message: str = "",
    agent_from: str = "",
    agent_to: str = "",
    tool_calls: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    ai_message_official: str = "",
) -> Dict[str, Any]:
    """Add an interaction to a test."""
    payload = {
        "test_id": test_id,
        "interaction_number": interaction_number,
        "user_message": user_message,
        "first_message": first_message,
        "agent_from": agent_from,
        "agent_to": agent_to,
        "tool_calls": tool_calls,
        "parameters": parameters or {},
        "ai_message_official": ai_message_official,
    }
    resp = httpx.post(
        _rest_url("agent_test_interactions"),
        headers=_headers(),
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()[0]


# ---------------------------------------------------------------------------
# agent_test_executions
# ---------------------------------------------------------------------------


def create_execution(test_id: str) -> Dict[str, Any]:
    """Create a new test execution with status 'pending'."""
    user_id = get_user_id()
    payload = {
        "test_id": test_id,
        "user_id": user_id,
        "status": "pending",
    }
    resp = httpx.post(
        _rest_url("agent_test_executions"),
        headers=_headers(),
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()[0]


def update_execution(
    execution_id: str, **fields: Any
) -> Dict[str, Any]:
    """Update execution fields (status, completed_at, tokens, etc.)."""
    resp = httpx.patch(
        _rest_url("agent_test_executions"),
        headers=_headers(),
        params={"id": f"eq.{execution_id}"},
        json=fields,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()[0]


def list_executions(test_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List executions, optionally filtered by test_id."""
    params: Dict[str, str] = {"select": "*", "order": "created_at.desc"}
    if test_id:
        params["test_id"] = f"eq.{test_id}"
    resp = httpx.get(
        _rest_url("agent_test_executions"),
        headers=_headers(),
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get a single execution by ID."""
    resp = httpx.get(
        _rest_url("agent_test_executions"),
        headers=_headers(),
        params={"select": "*", "id": f"eq.{execution_id}"},
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise Exception(f"Execution {execution_id} not found")
    return data[0]


# ---------------------------------------------------------------------------
# agent_execution_results
# ---------------------------------------------------------------------------


def insert_results(
    execution_id: str, results: List[Dict[str, Any]]
) -> int:
    """Insert execution results in batch. Returns count inserted."""
    if not results:
        return 0
    rows = []
    for r in results:
        rows.append(
            {
                "execution_id": execution_id,
                "interaction_number": r.get("interaction_number", 1),
                "sender": r.get("agent_name", ""),
                "content": r.get("actual_response", ""),
                "input_tokens": r.get("input_tokens", 0),
                "output_tokens": r.get("output_tokens", 0),
                "test_input": r.get("user_message", ""),
                "tester_ai": True,
            }
        )
    resp = httpx.post(
        _rest_url("agent_execution_results"),
        headers=_headers(),
        json=rows,
        timeout=30.0,
    )
    resp.raise_for_status()
    return len(rows)


def get_results(execution_id: str) -> List[Dict[str, Any]]:
    """Get all results for an execution."""
    resp = httpx.get(
        _rest_url("agent_execution_results"),
        headers=_headers(),
        params={
            "select": "*",
            "execution_id": f"eq.{execution_id}",
            "order": "interaction_number.asc",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()
