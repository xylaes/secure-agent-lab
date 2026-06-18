# STRIDE Threat Modeling Assessment: `shopping-assistant`

This document performs a systematic threat modeling assessment of the `shopping-assistant` codebase using the STRIDE methodology.

---

## 1. System Boundaries and Data Flows

### Entry Points
* **LLM Agent (`ShoppingHelper`)**: Receives natural language queries from users and interprets their shopping intent.
* **Agent Tool (`redeem_discount`)**: Intercepts queries involving discount codes and executes redemption logic.
* **Root Workflow (`shopping_assistant_workflow`)**: Routes events from `START` to `ShoppingHelper`.

### Data Storage
* **In-Memory Store (`DISCOUNT_STORE`)**: A simple global dictionary mapping discount codes (`"WELCOME50"`, `"SUMMER20"`) to their redemption status (`True`/`False`).

---

## 2. STRIDE Threat Analysis

### 👤 Spoofing (Identity Spoofing)
* **Threat**: The `redeem_discount` tool accepts `user_id: str` as an parameter supplied directly by the LLM.
* **Impact**: There is no cryptographic or session-based verification of the caller's identity. A user can claim any registered `user_id` string (e.g., `"admin_user"`, `"user_456"`) and the tool will execute the redemption under that identity.
* **Mitigation**: Implement token-based session verification (e.g., parsing a validated JWT token from the `Context` rather than relying on a raw string parameter).

### ✍️ Tampering (Data Modification)
* **Threat 1**: `DISCOUNT_STORE` is an in-memory dictionary. A restart of the application resets all redemption statuses back to `False`, allowing codes to be redeemed again.
* **Threat 2**: State modifications are done without locks or database-level transactions, exposing the system to race conditions (e.g., Time-of-Check to Time-of-Use / TOCTOU) where a code is redeemed twice via concurrent API calls.
* **Mitigation**: Use a persistent datastore (like Cloud SQL or Spanner) with transactional isolation levels (e.g., SELECT FOR UPDATE) to record redemptions.

### 📝 Repudiation (Audit Logging)
* **Threat**: There is no secure, tamper-resistant transaction logging when a discount code is successfully redeemed.
* **Impact**: In the event of fraudulent code usage, there is no audit trail to trace back which IP address, session ID, or actual client executed the transaction.
* **Mitigation**: Emit audit logs to a secure, write-only logging service (e.g., Cloud Logging) with details of the redemption.

### 🔓 Information Disclosure (Data Leakage)
* **Threat**: Line 11 of `app/agent.py` contains a hardcoded simulated credential: `api_key="AIzaSyD-mock-key-value-12345"`.
* **Impact**: Hardcoding credentials leaks them in plain text to the version control system (Git) and anyone with access to the source code.
* **Mitigation**: Remove the hardcoded `api_key` parameter from the Gemini constructor and use environment variables (e.g., `GEMINI_API_KEY`) or a secret manager.

### 🛑 Denial of Service (Resource Exhaustion)
* **Threat**: The agent workflow has no rate-limiting or concurrency control on expensive model calls and tool executions.
* **Impact**: An attacker can flood the agent with requests, causing massive API usage costs or exhausting server resource limits.
* **Mitigation**: Implement rate-limiting middleware at the FastAPI entry points.

### 🔑 Elevation of Privilege (Access Control Bypass)
* **Threat**: The `redeem_discount` tool performs a basic string check (`user_id.startswith("guest_")`) to block guest accounts.
* **Impact**: Any user can bypass this security check simply by choosing a `user_id` that does not start with `"guest_"`. They do not need to prove they are registered.
* **Mitigation**: Check the user ID against a verified database of registered accounts before allowing redemptions.
