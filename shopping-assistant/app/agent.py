# shopping-assistant/app/agent.py
from __future__ import annotations

from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.workflow import Edge, Workflow
from google.adk.agents.llm_agent import LlmAgent
from pydantic import BaseModel, Field

# Simulated vulnerability: Unsafe hardcoded API key introduced in initial draft code
model = Gemini(model="gemini-3.1-flash-lite", api_key="AIzaSyD-mock-key-value-12345")  # type: ignore

# In-memory discount redemption store (simulating database state)
DISCOUNT_STORE: dict[str, bool] = {"WELCOME50": False, "SUMMER20": False}


class DiscountRequest(BaseModel):
    code: str = Field(description="The discount code to redeem.")
    user_id: str = Field(description="The ID of the user requesting redemption.")


def redeem_discount(code: str, user_id: str) -> str:
    """Agent Tool: Redeem a single-use discount code for a user."""
    if code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."
    if DISCOUNT_STORE[code]:
        return "Error: Discount code has already been redeemed."
    if not user_id or user_id.startswith("guest_"):
        return "Error: Registered user account required to redeem discounts."

    DISCOUNT_STORE[code] = True
    return f"Success: Discount code {code} redeemed successfully for user {user_id}."


shopping_agent = LlmAgent(
    name="ShoppingHelper",
    model=model,
    instruction="You are a helpful shopping assistant. Use your tools to redeem discount codes for users.",
    tools=[redeem_discount],
)

root_workflow = Workflow(
    name="shopping_assistant_workflow",
    edges=[("START", shopping_agent)]
)

app = App(name="app", root_agent=root_workflow)
