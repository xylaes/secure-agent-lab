# 🔐 Secure Agent Lab — Google Secure Agentic Coding Codelab

This repository is the complete work product from the **[Secure Agentic Coding Codelab](https://codelabs.developers.google.com/secure-agentic-coding)** (June 2026).

It contains a fully scaffolded ADK 2.0 shopping assistant agent, hardened with a multi-layer security posture: pre-commit scanning, custom Semgrep rules, agent interception hooks, STRIDE threat modeling, and a TDD security test suite.

---

## 📁 Repository Structure

```
secure-agent-lab/
└── shopping-assistant/       # Core ADK 2.0 agent project
    ├── app/
    │   ├── agent.py               # ShoppingHelper agent + redeem_discount tool
    │   ├── agent_runtime_app.py   # Agent Engine deployment wrapper
    │   └── app_utils/             # Telemetry & typing helpers
    ├── .agents/
    │   ├── CONTEXT.md             # Secure coding standards & TDD planning gate
    │   ├── hooks.json             # PreToolUse interception hook config
    │   ├── scripts/
    │   │   └── validate_tool_call.py  # Hook script: blocks destructive shell commands
    │   └── skills/
    │       └── stride-threat-model/
    │           └── SKILL.md       # STRIDE threat modeling skill
    ├── .semgrep/
    │   └── rules.yaml             # Custom Semgrep rule: detects hardcoded Google API keys
    ├── .pre-commit-config.yaml    # Pre-commit hooks: whitespace + Semgrep scan
    ├── tests/
    │   └── test_agent.py          # Security test suite (pytest)
    ├── threat_model.md            # STRIDE threat model output
    └── pyproject.toml             # Project dependencies (uv)
```

---

## 🏗️ What Was Built — Step by Step

### Step 1 — Project Scaffolding

```bash
git init
git config user.name "Kaggle Student"
git config user.email "kaggle@student.dev"

cd shopping-assistant
uvx google-agents-cli create shopping-assistant --template adk
$env:UV_LINK_MODE="copy"; uv sync
```

- Used `agents-cli 0.5.0` to scaffold an ADK 2.0 ReAct agent project.
- Set `UV_LINK_MODE=copy` to work around Windows/OneDrive hardlink restrictions.
- Fixed a scaffolding bug: replaced the non-existent `Edge.chain(...)` syntax with ADK 2.0's tuple-based `edges=[("START", shopping_agent)]`.
- Fixed the `App(name=...)` mismatch by aligning the name to `"app"` (matching the folder name), resolving `SessionNotFoundError` during the dev server session lookup.

---

### Step 2 — Agent Implementation

**File: [`shopping-assistant/app/agent.py`](./shopping-assistant/app/agent.py)**

The agent implements:
- A `ShoppingHelper` `LlmAgent` powered by `gemini-3.1-flash-lite`.
- A `redeem_discount(code, user_id) -> str` tool with the following business logic guardrails:
  - Rejects unknown discount codes (not in `DISCOUNT_STORE`).
  - Rejects already-redeemed codes (single-use enforcement).
  - Rejects guest accounts (`user_id.startswith("guest_")`).
- A **deliberate simulated vulnerability**: a hardcoded `api_key="AIzaSyD-mock-key-value-12345"` on the `Gemini(...)` constructor — inserted intentionally to demonstrate that pre-commit security scanning catches it.

```python
# Simulated vulnerability: Unsafe hardcoded API key introduced in initial draft code
model = Gemini(model="gemini-3.1-flash-lite", api_key="AIzaSyD-mock-key-value-12345")  # type: ignore
```

> ⚠️ **This key is intentionally fake and is present to demonstrate the Semgrep pre-commit block.**

---

### Step 3 — Security Hardening Layer

#### 3a. Secure Coding Standards (`CONTEXT.md`)

**File: [`.agents/CONTEXT.md`](./shopping-assistant/.agents/CONTEXT.md)**

Defines three paved-road rules enforced at the planning/coding agent level:
1. **Tool Input Validation** — all agent tools must use Pydantic schemas.
2. **No Shell Execution** — raw shell commands are blocked unless approved by `hooks.json`.
3. **Pre-Commit Remediation Loop** — any Semgrep failure must be treated as a refactoring task.

Also includes a **TDD Planning Gate**: every implementation plan must include a dedicated *Security Boundaries & Assertions* section.

#### 3b. Custom Semgrep Rule

**File: [`.semgrep/rules.yaml`](./shopping-assistant/.semgrep/rules.yaml)**

```yaml
rules:
  - id: detect-hardcoded-google-api-key
    pattern-regex: 'AIzaSy[A-Za-z0-9_\-]*'
    message: "Security violation: Hardcoded Google API key detected."
    languages: [python]
    severity: ERROR
```

Detects any literal Google API key (`AIzaSy...`) in Python source files and blocks the commit.

#### 3c. Pre-Commit Configuration

**File: [`.pre-commit-config.yaml`](./shopping-assistant/.pre-commit-config.yaml)**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
  - repo: local
    hooks:
      - id: semgrep-local
        name: Semgrep Scan
        entry: uv run --directory shopping-assistant semgrep --config .semgrep/rules.yaml --error
        language: system
        types: [python]
        pass_filenames: false
```

The Semgrep hook is configured at the **repo root** (one level above `shopping-assistant`) and uses `--directory` to target the subdirectory. It **successfully blocks** the commit when the mock API key is present.

#### 3d. Agent Interception Hook

**File: [`.agents/hooks.json`](./shopping-assistant/.agents/hooks.json)**

```json
{
  "enabled": true,
  "PreToolUse": [
    {
      "matcher": "run_command",
      "command": "python3 .agents/scripts/validate_tool_call.py",
      "timeout": 10
    }
  ]
}
```

Every `run_command` tool call is intercepted by `validate_tool_call.py`, which reads the proposed command and exits with code `1` (blocking execution) if it matches destructive patterns like `rm -rf`.

---

### Step 4 — STRIDE Threat Model

**File: [`threat_model.md`](./shopping-assistant/threat_model.md)**

Executed the `stride-threat-model` skill against the shopping assistant graph. The model identified 6 threat categories:

| STRIDE Category | Finding |
|---|---|
| **Spoofing** | `user_id` is not cryptographically verified — any string is accepted |
| **Tampering** | In-memory `DISCOUNT_STORE` resets on restart; race condition (TOCTOU) possible |
| **Repudiation** | No tamper-resistant audit log for successful redemptions |
| **Information Disclosure** | Hardcoded `api_key` leaks credentials to version control |
| **Denial of Service** | No rate-limiting on model calls or tool executions |
| **Elevation of Privilege** | `guest_` check is a string prefix — easily bypassed by crafting any other `user_id` |

---

### Step 5 — TDD Security Test Suite

**File: [`tests/test_agent.py`](./shopping-assistant/tests/test_agent.py)**

Written to verify all security boundary findings from the STRIDE model:

```bash
uv run pytest tests/test_agent.py
# ======================== 3 passed in 3.57s ========================
```

| Test | Asserts |
|---|---|
| `test_discount_code_can_only_be_redeemed_once` | First redemption succeeds; second with same code is rejected |
| `test_discount_redemption_rejects_invalid_code` | Unknown codes return `Error: Invalid discount code` |
| `test_discount_redemption_rejects_guest_accounts` | `guest_*` user IDs are blocked; store state is unchanged |

The fixture uses `autouse=True` to fully reset `DISCOUNT_STORE` between every test for strict isolation.

---

### Step 6 — ADK Dev UI Playground

The agent dev server was successfully started:

```bash
uv run adk web app --host 127.0.0.1 --port 8080
# ADK Web Server started — http://127.0.0.1:8080
```

The playground at `http://127.0.0.1:8080/dev-ui/?app=app` confirms:
- The `ShoppingHelper` agent graph renders correctly (`START → ShoppingHelper → redeem_discount → END`).
- A test message was sent and the agent attempted model inference.
- The `400 INVALID_ARGUMENT: API key not valid` error is the **expected and intentional** result — it proves the hardcoded mock key `AIzaSyD-mock-key-value-12345` is being picked up by the model client, and is not a real credential that would ever succeed.

---

## 🔑 Key Technical Notes & Gotchas

| Problem | Root Cause | Fix Applied |
|---|---|---|
| `uv sync` fails on Windows | OneDrive filesystem blocks hardlinks | `$env:UV_LINK_MODE="copy"` |
| `Edge.chain(...)` AttributeError | Method doesn't exist in ADK 2.0 | Replaced with `edges=[("START", agent)]` tuple notation |
| `SessionNotFoundError` in dev server | `App(name="shopping_assistant")` mismatches folder name `app` | Changed to `App(name="app")` |
| Pre-commit hook not finding Semgrep | Hook runs from repo root, one level above the project | Used `uv run --directory shopping-assistant semgrep` |
| `agents-cli playground` fails | CLI globs current directory contents into `adk web` args | Use `uv run adk web app` directly instead |
| API key `api_key=` not a `Gemini` field | ADK 2.0 `Gemini` class dropped `api_key` from its schema | The `# type: ignore` suppresses the Pydantic validation warning for the codelab demo |

---

## 🚀 Running It Yourself

### Prerequisites
- Python 3.11–3.13
- [`uv`](https://docs.astral.sh/uv/)
- `uvx google-agents-cli`
- A real `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/app/apikey) — or Google Cloud ADC for Vertex AI

### Install
```bash
$env:UV_LINK_MODE="copy"
cd shopping-assistant
uv sync
```

### Run Security Tests
```bash
uv run pytest tests/test_agent.py
```

### Run the Dev Playground
```bash
# Set a real key first (replace the mock in app/agent.py)
uv run adk web app --host 127.0.0.1 --port 8080
# Open: http://127.0.0.1:8080/dev-ui/?app=app
```

---

## 📚 References

- [Secure Agentic Coding Codelab](https://codelabs.developers.google.com/secure-agentic-coding)
- [Google Agent Development Kit (ADK)](https://adk.dev/)
- [google-agents-cli](https://pypi.org/project/google-agents-cli/)
- [Semgrep](https://semgrep.dev/)
- [STRIDE Threat Modeling](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
