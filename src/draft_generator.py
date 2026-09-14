"""
draft_generator.py — MarginGuard

Given a margin alert dict, uses the Strands/Bedrock agent to generate natural,
Ghanaian small-business tone draft messages for either:
  - is_negotiable=True:  a supplier negotiation message + a new storefront price caption
  - is_negotiable=False: a customer-facing price increase notice
"""

from strands import Agent
from strands.models import BedrockModel

MODEL_ID = "arn:aws:bedrock:us-east-1:757235735623:inference-profile/us.anthropic.claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a communications assistant for a small Ghanaian artisan or trader.
Your job is to write short, warm, professional draft messages in the voice of a real Ghanaian
small-business owner. Use simple English with a touch of natural Ghanaian phrasing — greetings
like "Hello boss", "Good day madam/sir", light use of "ooo", "please", "God bless" where
it sounds authentic — but keep it professional and readable. Never write pidgin that sounds
mocking or stereotyped. Be concise: each draft should be 3-6 sentences max.

You output ONLY valid JSON, no prose before or after. The schema depends on context:

If is_negotiable is true, output:
{
  "negotiation_message": "Draft message to send to the supplier asking to negotiate the price",
  "storefront_caption": "Draft notice to update the product's price on the storefront or WhatsApp status"
}

If is_negotiable is false, output:
{
  "customer_notice": "Draft message to send to customers explaining the price increase"
}
"""

_model = None
_agent = None

def _get_agent():
    global _model, _agent
    if _agent is None:
        _model = BedrockModel(model_id=MODEL_ID, region_name="us-east-1")
        _agent = Agent(model=_model, system_prompt=SYSTEM_PROMPT)
    return _agent


def generate_drafts(alert: dict) -> dict:
    """
    Parameters
    ----------
    alert : dict with keys:
        material     (str)   — e.g. "flour"
        old_price    (float) — previous unit price in GHS
        new_price    (float) — new unit price in GHS
        pct_change   (float) — percentage increase
        is_negotiable (bool) — whether supplier price can be negotiated

    Returns
    -------
    dict with keys depending on is_negotiable:
        negotiation_message + storefront_caption   (if is_negotiable)
        customer_notice                            (if not is_negotiable)
    """
    import json

    material     = alert["material"]
    old_price    = alert["old_price"]
    new_price    = alert["new_price"]
    pct_change   = alert["pct_change"]
    is_negotiable = alert["is_negotiable"]

    prompt = (
        f"Material: {material}\n"
        f"Old unit price: GHS {old_price}\n"
        f"New unit price: GHS {new_price}\n"
        f"Price increase: {pct_change}%\n"
        f"is_negotiable: {str(is_negotiable).lower()}\n\n"
        "Generate the appropriate draft message(s) as JSON per the schema."
    )

    agent = _get_agent()
    response = agent(prompt)

    # agent() returns an AgentResult; get the text content
    raw = str(response).strip()

    # Strip markdown code fences if the model wraps the JSON
    if raw.startswith("```"):
        lines = raw.split("\n")
        # drop first and last fence lines
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return json.loads(raw)


# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    sample_negotiable = {
        "material": "flour",
        "old_price": 150.0,
        "new_price": 200.0,
        "pct_change": 33.3,
        "is_negotiable": True,
    }
    sample_fixed = {
        "material": "cooking gas",
        "old_price": 180.0,
        "new_price": 220.0,
        "pct_change": 22.2,
        "is_negotiable": False,
    }

    print("=== Test 1: negotiable material (flour) ===")
    drafts1 = generate_drafts(sample_negotiable)
    print(json.dumps(drafts1, indent=2))

    print("\n=== Test 2: non-negotiable material (cooking gas) ===")
    drafts2 = generate_drafts(sample_fixed)
    print(json.dumps(drafts2, indent=2))
