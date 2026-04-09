# -*- coding: utf-8 -*-
"""Tests for CLI commands."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from monkai_hub_cli.main import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MonkAI Hub CLI" in result.stdout


def test_login_missing_credentials():
    result = runner.invoke(
        app, ["login"], env={"MONKAI_EMAIL": "", "MONKAI_PASSWORD": ""}
    )
    assert result.exit_code == 1
    parsed = json.loads(result.stdout)
    assert parsed["code"] == "AUTH_ERROR"


@patch("monkai_hub_cli.auth.login")
def test_login_success(mock_login):
    mock_login.return_value = {
        "user_id": "uuid-123",
        "email": "test@monkai.com.br",
        "expires_at": 9999999999,
    }
    result = runner.invoke(
        app, ["login", "--email", "test@monkai.com.br", "--password", "pass123"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "ok"
    assert parsed["email"] == "test@monkai.com.br"


@patch("monkai_hub_cli.auth.logout")
def test_logout(mock_logout):
    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "ok"


@patch("monkai_hub_cli.supabase_client.list_tests")
@patch("monkai_hub_cli.supabase_client.get_token")
def test_test_list(mock_token, mock_list):
    mock_token.return_value = "fake-jwt"
    mock_list.return_value = [
        {"id": "t1", "name": "Test1", "test_type": "service", "status": "draft", "agent_name": "gigi", "created_at": "2026-01-01"},
    ]
    result = runner.invoke(app, ["test", "list"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["count"] == 1
    assert parsed["tests"][0]["id"] == "t1"


@patch("monkai_hub_cli.supabase_client.create_test")
@patch("monkai_hub_cli.supabase_client.get_user_id")
@patch("monkai_hub_cli.supabase_client.get_token")
def test_test_create(mock_token, mock_uid, mock_create):
    mock_token.return_value = "fake-jwt"
    mock_uid.return_value = "user-123"
    mock_create.return_value = {"id": "new-test-id", "name": "My Test"}
    result = runner.invoke(
        app,
        ["test", "create", "--name", "My Test", "--api-url", "https://api.test.com"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["test_id"] == "new-test-id"


@patch("monkai_hub_cli.supabase_client.insert_results")
@patch("monkai_hub_cli.supabase_client.update_execution")
@patch("monkai_hub_cli.supabase_client.create_execution")
@patch("monkai_hub_cli.supabase_client.get_interactions")
@patch("monkai_hub_cli.supabase_client.get_test")
@patch("monkai_hub_cli.tester_client.execute_test")
@patch("monkai_hub_cli.supabase_client.get_user_id")
@patch("monkai_hub_cli.supabase_client.get_token")
def test_test_run(mock_token, mock_uid, mock_execute, mock_get_test, mock_get_inter,
                  mock_create_exec, mock_update_exec, mock_insert):
    mock_token.return_value = "fake-jwt"
    mock_uid.return_value = "user-123"
    mock_get_test.return_value = {
        "id": "t1", "api_url": "https://api.test.com",
        "headers": {}, "data_template": {},
    }
    mock_get_inter.return_value = [
        {"id": "i1", "user_message": "Hello", "interaction_number": 1,
         "first_message": "", "agent_to": "", "tool_calls": "", "parameters": {}},
    ]
    mock_create_exec.return_value = {"id": "exec-1"}
    mock_update_exec.return_value = {"id": "exec-1"}
    mock_execute.return_value = {
        "success": True,
        "results": [{"user_message": "Hello", "actual_response": "Hi", "status": "success",
                      "input_tokens": 10, "output_tokens": 20, "agent_name": "gigi"}],
        "kpi_report": {"total_tests": 1, "passed": 1, "failed": 0, "success_rate": 100,
                       "avg_response_time_ms": 500, "total_input_tokens": 10, "total_output_tokens": 20},
    }
    mock_insert.return_value = 1

    result = runner.invoke(app, ["test", "run", "t1"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "ok"
    assert parsed["execution_id"] == "exec-1"
    assert parsed["passed"] == 1


@patch("monkai_hub_cli.supabase_client.get_results")
@patch("monkai_hub_cli.supabase_client.get_execution")
@patch("monkai_hub_cli.supabase_client.get_token")
def test_test_results(mock_token, mock_exec, mock_results):
    mock_token.return_value = "fake-jwt"
    mock_exec.return_value = {"id": "exec-1", "status": "completed"}
    mock_results.return_value = [
        {"interaction_number": 1, "content": "Hi", "sender": "gigi"},
    ]
    result = runner.invoke(app, ["test", "results", "exec-1"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["result_count"] == 1
