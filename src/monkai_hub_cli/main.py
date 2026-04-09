# -*- coding: utf-8 -*-
"""MonkAI Hub CLI — entry point."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

from monkai_hub_cli.output import print_error, print_success

app = typer.Typer(
    name="monkai-hub",
    help="MonkAI Hub CLI — configure, run and manage agent tests.",
    add_completion=False,
    pretty_exceptions_enable=False,
)

test_app = typer.Typer(help="Manage agent tests.")
app.add_typer(test_app, name="test")


# ---------------------------------------------------------------------------
# monkai-hub login / logout
# ---------------------------------------------------------------------------


@app.command()
def login(
    email: Optional[str] = typer.Option(None, help="Email (or env MONKAI_EMAIL)."),
    password: Optional[str] = typer.Option(None, help="Password (or env MONKAI_PASSWORD)."),
) -> None:
    """Authenticate with MonkAI Hub."""
    from monkai_hub_cli.auth import login as do_login

    resolved_email = email or os.environ.get("MONKAI_EMAIL", "")
    resolved_password = password or os.environ.get("MONKAI_PASSWORD", "")

    if not resolved_email or not resolved_password:
        print_error(
            "Email and password required. Use --email/--password or set MONKAI_EMAIL/MONKAI_PASSWORD.",
            code="AUTH_ERROR",
        )

    try:
        session = do_login(resolved_email, resolved_password)
    except Exception as exc:
        print_error(str(exc), code="AUTH_ERROR")

    print_success(
        user_id=session["user_id"],
        email=session["email"],
        expires_at=session.get("expires_at"),
    )


@app.command()
def logout() -> None:
    """Remove stored credentials."""
    from monkai_hub_cli.auth import logout as do_logout

    do_logout()
    print_success(message="Logged out")


# ---------------------------------------------------------------------------
# monkai-hub test create
# ---------------------------------------------------------------------------


@test_app.command("create")
def test_create(
    name: str = typer.Option(..., help="Test name."),
    api_url: str = typer.Option(..., "--api-url", help="API endpoint to test."),
    description: str = typer.Option("", help="Test description."),
    headers: Optional[str] = typer.Option(None, help="HTTP headers as JSON string."),
    body_template: Optional[str] = typer.Option(None, "--body-template", help="Body template as JSON."),
    agent_name: str = typer.Option("", "--agent-name", help="Agent name."),
    test_type: str = typer.Option("service", "--type", help="Test type (service/local)."),
    repeat_count: int = typer.Option(1, "--repeat", help="Repeat count."),
    interactions: Optional[str] = typer.Option(
        None, help="Interactions as JSON array: [{\"user_message\":\"Hi\",\"ai_message_official\":\"Hello\"}]"
    ),
) -> None:
    """Create a new agent test in the Hub."""
    from monkai_hub_cli import supabase_client as sb

    parsed_headers = {}
    if headers:
        try:
            parsed_headers = json.loads(headers)
        except json.JSONDecodeError as e:
            print_error(f"Invalid headers JSON: {e}", code="VALIDATION_ERROR")

    parsed_template = {}
    if body_template:
        try:
            parsed_template = json.loads(body_template)
        except json.JSONDecodeError as e:
            print_error(f"Invalid body-template JSON: {e}", code="VALIDATION_ERROR")

    try:
        test = sb.create_test(
            name=name,
            test_type=test_type,
            description=description,
            api_url=api_url,
            headers=parsed_headers,
            data_template=parsed_template,
            agent_name=agent_name,
            repeat_count=repeat_count,
        )
    except Exception as exc:
        print_error(f"Failed to create test: {exc}", code="HUB_ERROR")

    test_id = test["id"]

    # Add interactions if provided
    interaction_count = 0
    if interactions:
        try:
            items = json.loads(interactions)
        except json.JSONDecodeError as e:
            print_error(f"Invalid interactions JSON: {e}", code="VALIDATION_ERROR")

        for i, item in enumerate(items, start=1):
            try:
                sb.add_interaction(
                    test_id=test_id,
                    interaction_number=i,
                    user_message=item.get("user_message", ""),
                    first_message=item.get("first_message", ""),
                    agent_to=item.get("agent_to", ""),
                    tool_calls=item.get("tool_calls", ""),
                    parameters=item.get("parameters"),
                    ai_message_official=item.get("ai_message_official", ""),
                )
                interaction_count += 1
            except Exception as exc:
                print_error(f"Failed to add interaction {i}: {exc}", code="HUB_ERROR")

    print_success(
        test_id=test_id,
        name=name,
        interactions=interaction_count,
    )


# ---------------------------------------------------------------------------
# monkai-hub test add-interaction
# ---------------------------------------------------------------------------


@test_app.command("add-interaction")
def test_add_interaction(
    test_id: str = typer.Argument(..., help="Test ID."),
    user_message: str = typer.Option(..., "--message", help="User message."),
    interaction_number: int = typer.Option(..., "--number", help="Interaction number."),
    expected_response: str = typer.Option("", "--expected", help="Expected AI response."),
    expected_sender: str = typer.Option("", "--sender", help="Expected sender/agent name."),
    tool_calls: str = typer.Option("", "--tool-calls", help="Expected tool calls."),
    parameters: Optional[str] = typer.Option(None, "--parameters", help="Expected parameters as JSON."),
) -> None:
    """Add an interaction to an existing test."""
    from monkai_hub_cli import supabase_client as sb

    parsed_params = None
    if parameters:
        try:
            parsed_params = json.loads(parameters)
        except json.JSONDecodeError as e:
            print_error(f"Invalid parameters JSON: {e}", code="VALIDATION_ERROR")

    try:
        interaction = sb.add_interaction(
            test_id=test_id,
            interaction_number=interaction_number,
            user_message=user_message,
            agent_to=expected_sender,
            tool_calls=tool_calls,
            parameters=parsed_params,
            ai_message_official=expected_response,
        )
    except Exception as exc:
        print_error(f"Failed to add interaction: {exc}", code="HUB_ERROR")

    print_success(
        interaction_id=interaction["id"],
        test_id=test_id,
        interaction_number=interaction_number,
    )


# ---------------------------------------------------------------------------
# monkai-hub test list
# ---------------------------------------------------------------------------


@test_app.command("list")
def test_list() -> None:
    """List all tests for the authenticated user."""
    from monkai_hub_cli import supabase_client as sb

    try:
        tests = sb.list_tests()
    except Exception as exc:
        print_error(f"Failed to list tests: {exc}", code="HUB_ERROR")

    items = []
    for t in tests:
        items.append(
            {
                "id": t["id"],
                "name": t["name"],
                "test_type": t.get("test_type", ""),
                "status": t.get("status", ""),
                "agent_name": t.get("agent_name", ""),
                "created_at": t.get("created_at", ""),
            }
        )

    print_success(tests=items, count=len(items))


# ---------------------------------------------------------------------------
# monkai-hub test get
# ---------------------------------------------------------------------------


@test_app.command("get")
def test_get(
    test_id: str = typer.Argument(..., help="Test ID."),
) -> None:
    """Get test details including interactions."""
    from monkai_hub_cli import supabase_client as sb

    try:
        test = sb.get_test(test_id)
        interactions = sb.get_interactions(test_id)
    except Exception as exc:
        print_error(f"Failed to get test: {exc}", code="HUB_ERROR")

    print_success(
        test=test,
        interactions=interactions,
        interaction_count=len(interactions),
    )


# ---------------------------------------------------------------------------
# monkai-hub test run
# ---------------------------------------------------------------------------


@test_app.command("run")
def test_run(
    test_id: str = typer.Argument(..., help="Test ID to execute."),
    model: Optional[str] = typer.Option(None, help="Model override."),
    timeout: int = typer.Option(120, help="Timeout per interaction in seconds."),
) -> None:
    """Execute a test remotely via the MonkAI Tester server."""
    from monkai_hub_cli import supabase_client as sb
    from monkai_hub_cli.tester_client import execute_test

    # Get test config
    try:
        test = sb.get_test(test_id)
        interactions = sb.get_interactions(test_id)
    except Exception as exc:
        print_error(f"Failed to fetch test: {exc}", code="HUB_ERROR")

    if not interactions:
        print_error("Test has no interactions. Add interactions first.", code="VALIDATION_ERROR")

    # Build dev config from test
    dev_config = {
        "apiUrl": test.get("api_url", ""),
        "headers": test.get("headers", {}),
        "bodyTemplate": test.get("data_template", {}),
    }

    if not dev_config["apiUrl"]:
        print_error("Test has no api_url configured.", code="VALIDATION_ERROR")

    # Create execution
    try:
        execution = sb.create_execution(test_id)
        execution_id = execution["id"]
        sb.update_execution(
            execution_id,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        print_error(f"Failed to create execution: {exc}", code="HUB_ERROR")

    # Build interactions payload for tester server
    tester_interactions = []
    for inter in interactions:
        tester_interactions.append(
            {
                "id": inter.get("id"),
                "user_message": inter.get("user_message", ""),
                "first_message": inter.get("first_message", ""),
                "ai_message_official": inter.get("ai_message_official", ""),
                "sender_official": inter.get("agent_to", ""),
                "tool_calls_official": inter.get("tool_calls", ""),
                "parameters_official": inter.get("parameters"),
                "interaction_number": inter.get("interaction_number", 1),
            }
        )

    # Execute via Railway server
    try:
        result = execute_test(
            test_id=test_id,
            execution_id=execution_id,
            interactions=tester_interactions,
            dev_config=dev_config,
            timeout=float(timeout),
        )
    except Exception as exc:
        sb.update_execution(
            execution_id,
            status="failed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            error_message=str(exc),
        )
        print_error(f"Test execution failed: {exc}", code="REMOTE_ERROR")

    # Save results to Supabase
    kpi = result.get("kpi_report", {})
    csv_results = result.get("results", [])

    try:
        sb.update_execution(
            execution_id,
            status="completed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            total_interactions=len(csv_results),
            input_tokens=kpi.get("total_input_tokens", 0),
            output_tokens=kpi.get("total_output_tokens", 0),
        )
        sb.insert_results(execution_id, csv_results)
    except Exception as exc:
        print_error(f"Failed to save results: {exc}", code="HUB_ERROR")

    total = kpi.get("total_tests", len(csv_results))
    passed = kpi.get("passed", 0)
    failed = kpi.get("failed", 0)

    print_success(
        execution_id=execution_id,
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=round(kpi.get("success_rate", 0) / 100, 4) if kpi.get("success_rate") else 0,
    )


# ---------------------------------------------------------------------------
# monkai-hub test results
# ---------------------------------------------------------------------------


@test_app.command("results")
def test_results(
    execution_id: str = typer.Argument(..., help="Execution ID."),
) -> None:
    """Show results of a test execution."""
    from monkai_hub_cli import supabase_client as sb

    try:
        execution = sb.get_execution(execution_id)
        results = sb.get_results(execution_id)
    except Exception as exc:
        print_error(f"Failed to fetch results: {exc}", code="HUB_ERROR")

    print_success(
        execution=execution,
        results=results,
        result_count=len(results),
    )


# ---------------------------------------------------------------------------
# monkai-hub test executions
# ---------------------------------------------------------------------------


@test_app.command("executions")
def test_executions(
    test_id: Optional[str] = typer.Argument(None, help="Filter by test ID."),
) -> None:
    """List test executions."""
    from monkai_hub_cli import supabase_client as sb

    try:
        executions = sb.list_executions(test_id)
    except Exception as exc:
        print_error(f"Failed to list executions: {exc}", code="HUB_ERROR")

    items = []
    for e in executions:
        items.append(
            {
                "id": e["id"],
                "test_id": e.get("test_id", ""),
                "status": e.get("status", ""),
                "total_interactions": e.get("total_interactions"),
                "input_tokens": e.get("input_tokens"),
                "output_tokens": e.get("output_tokens"),
                "started_at": e.get("started_at", ""),
                "completed_at": e.get("completed_at"),
            }
        )

    print_success(executions=items, count=len(items))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
