# monkai-hub-cli

CLI for MonkAI Hub — configure, run and manage agent tests from the terminal.

## Install

```bash
pip install monkai-hub-cli
```

## Usage

```bash
# Login
monkai-hub login --email you@company.com --password ***

# Create a test
monkai-hub test create --name "My Test" --api-url https://api.example.com

# Add interactions
monkai-hub test add-interaction <test-id> --message "Hello" --number 1 --expected "Hi there"

# Run test remotely
monkai-hub test run <test-id>

# See results
monkai-hub test results <execution-id>

# List tests
monkai-hub test list
```
