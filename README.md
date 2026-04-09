# monkai-hub-cli

[![PyPI](https://img.shields.io/pypi/v/monkai-hub-cli.svg)](https://pypi.org/project/monkai-hub-cli/)
[![Python](https://img.shields.io/pypi/pyversions/monkai-hub-cli.svg)](https://pypi.org/project/monkai-hub-cli/)
[![License](https://img.shields.io/pypi/l/monkai-hub-cli.svg)](https://github.com/BeMonkAI/monkai-hub-cli/blob/main/LICENSE)

Command-line interface for [MonkAI Hub](https://www.monkaihub.com) — configure, run and manage agent tests directly from your terminal.

Designed to be operated by AI assistants (Claude Code, Copilot, Cursor) and developers who prefer the terminal over the web UI. All output is JSON for easy parsing and scripting.

---

## Why a CLI?

The MonkAI Hub web dashboard is great for browsing results and visual analysis. But when you want to:

- **Create dozens of test cases programmatically** instead of clicking through forms
- **Run tests from CI/CD pipelines** without browser automation
- **Let an AI assistant configure and execute tests** based on a natural-language description
- **Script test execution** as part of a larger workflow
- **Compare runs across different models** in a reproducible way

…the CLI is the right tool. Everything you can do in the Hub UI for testing, you can do here — without leaving your terminal.

---

## Installation

```bash
pip install monkai-hub-cli
```

Requires Python 3.9 or newer. Verify the install:

```bash
monkai-hub --help
```

---

## Quick start

### 1. Authenticate

Log in with your MonkAI Hub credentials. The CLI saves a JWT to `~/.monkai-hub/auth.json` and refreshes it automatically.

```bash
monkai-hub login --email you@company.com --password your-password
```

You can also export credentials as environment variables to avoid typing them every time:

```bash
export MONKAI_EMAIL=you@company.com
export MONKAI_PASSWORD=your-password
monkai-hub login
```

### 2. Create a test

```bash
monkai-hub test create \
  --name "Greeting Test" \
  --api-url https://my-agent.example.com/chat \
  --headers '{"Authorization":"Bearer abc123"}' \
  --interactions '[
    {"user_message":"Hello","ai_message_official":"Hi there!"},
    {"user_message":"How are you?","ai_message_official":"I am well, thanks!"}
  ]'
```

The response includes the new `test_id` — copy it for the next steps.

### 3. Run the test

The execution happens on the MonkAI Tester server (proxied via the Hub's Edge Function — no API keys needed in the CLI):

```bash
monkai-hub test run <test-id>
```

You get back the execution summary: `total`, `passed`, `failed`, `pass_rate`, and an `execution_id`.

### 4. View the results

```bash
monkai-hub test results <execution-id>
```

The full execution metadata plus every individual result row, ready to be piped into `jq` or any other JSON processor.

---

## Commands

### Authentication

| Command | Description |
|---------|-------------|
| `monkai-hub login` | Authenticate with MonkAI Hub. Stores JWT locally. |
| `monkai-hub logout` | Remove stored credentials. |

### Test management

| Command | Description |
|---------|-------------|
| `monkai-hub test create` | Create a new agent test, optionally with interactions. |
| `monkai-hub test add-interaction <test-id>` | Append a new interaction to an existing test. |
| `monkai-hub test list` | List all your tests. |
| `monkai-hub test get <test-id>` | Show test details and all interactions. |

### Execution

| Command | Description |
|---------|-------------|
| `monkai-hub test run <test-id>` | Execute a test remotely via the MonkAI Tester server. |
| `monkai-hub test results <execution-id>` | Show all results from an execution. |
| `monkai-hub test executions [test-id]` | List executions, optionally filtered by test. |

Run `monkai-hub <command> --help` on any command for the full option list.

---

## Output format

Every command writes a JSON document to stdout. Success looks like this:

```json
{
  "status": "ok",
  "test_id": "abc-123",
  "name": "Greeting Test",
  "interactions": 2
}
```

Errors include a stable error code so scripts can branch on the failure type:

```json
{
  "status": "error",
  "code": "AUTH_ERROR",
  "message": "Login failed: Invalid login credentials"
}
```

| Code | When |
|------|------|
| `AUTH_ERROR` | Login failed or token expired and refresh failed. |
| `VALIDATION_ERROR` | A flag value (JSON, etc.) is malformed. |
| `HUB_ERROR` | Supabase request failed (network, RLS, invalid IDs). |
| `REMOTE_ERROR` | Test execution on the Tester server failed. |

Exit code is `0` on success, `1` on any error.

---

## How it works

The CLI is a thin HTTP wrapper. It does not import any internal MonkAI library — every operation is a REST call:

```
monkai-hub-cli
    │
    ├── auth.py            ──>  Supabase Auth (email/password → JWT)
    │
    ├── supabase_client.py ──>  Supabase REST API
    │                            (agent_tests, agent_test_interactions,
    │                             agent_test_executions, agent_execution_results)
    │
    └── tester_client.py   ──>  Supabase Edge Function (python-test-executor)
                                 │
                                 └──>  MonkAI Tester (Railway server)
```

All credentials stay server-side. The CLI only ever holds the user's JWT, which is bound to that user's Row Level Security policies in Supabase. There is no API key for the Tester server in the CLI — the Edge Function holds it and gates access by JWT.

---

## Use with AI assistants

The JSON-only output is intentional: AI assistants (Claude Code, Cursor, Copilot CLI, etc.) can call the CLI, parse the response, and chain commands without screen-scraping or fragile text parsing.

Example prompt to an assistant:

> "Create a test in MonkAI Hub for the agent at `https://my-agent.example.com/chat`. Use these three interactions: greet the user, ask for their order number, confirm the order. Then run the test and show me the results."

The assistant runs `monkai-hub test create`, captures the `test_id` from the JSON, runs `monkai-hub test run`, captures the `execution_id`, and finally calls `monkai-hub test results` — all without human intervention.

---

## Contributing

Issues and pull requests are welcome at [github.com/BeMonkAI/monkai-hub-cli](https://github.com/BeMonkAI/monkai-hub-cli).

```bash
git clone https://github.com/BeMonkAI/monkai-hub-cli.git
cd monkai-hub-cli
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install pytest
pytest tests/ -v
```

---

## Links

- **MonkAI Hub:** https://www.monkaihub.com
- **PyPI package:** https://pypi.org/project/monkai-hub-cli/
- **Issues:** https://github.com/BeMonkAI/monkai-hub-cli/issues

---

## License

MIT — see [LICENSE](LICENSE).
