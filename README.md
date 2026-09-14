# MarginGuard 📊

> **AI margin tracker for Ghanaian artisans — built with AWS Strands Agents SDK + Amazon Bedrock**

MarginGuard helps small Ghanaian artisans and traders survive rising supplier costs. They paste a raw WhatsApp message from a supplier, and MarginGuard automatically parses the prices, tracks margin changes, and — when a price spike is detected — drafts a supplier negotiation message *and* a customer-facing price-update notice, all in natural Ghanaian small-business tone.

---

## The Problem

Small artisans in Ghana receive supplier price updates via WhatsApp in informal, pidgin-heavy text:

> *"boss flour price don go up ooo — 3 bags now 600 cedis, transport 20"*

Manually tracking whether this affects their margins, updating storefront prices, and communicating changes to customers is time-consuming and error-prone. Most just absorb the cost or reprice by gut feeling.

---

## What MarginGuard Does

```
Supplier WhatsApp message
        │
        ▼
┌──────────────────────┐
│   Parser Agent       │  Strands Agent + Claude on Bedrock
│   (parser_agent.py)  │  Extracts: material, qty, unit_price,
│                      │  surcharges, confidence, currency
└──────────┬───────────┘
           │  structured JSON
           ▼
┌──────────────────────┐
│   Price DB           │  SQLite — materials + price_history
│   (db.py)            │  Detects ≥10% price spike → margin alert
└──────────┬───────────┘
           │  alert dict  (only when spike detected)
           ▼
┌──────────────────────┐
│   Draft Generator    │  Strands Agent + Claude on Bedrock
│   (draft_generator)  │  Negotiable supplier? → negotiation msg
│                      │  Fixed price?        → customer notice
└──────────────────────┘
```

### Key Features

| Feature | Detail |
|---|---|
| **Informal text parsing** | Handles pidgin, local units (bags, olonka, gallon, yard), informal address terms (boss, chief, sister) |
| **Confidence routing** | Low-confidence extractions go to a `review_queue` instead of silently corrupting data |
| **Margin alerting** | Fires when unit price increases ≥ 10% vs. last recorded price |
| **AI draft generation** | Generates supplier negotiation *or* customer price notice — natural Ghanaian business tone, not templates |
| **Persistent price history** | Every price event recorded; materials table shows current state across sessions |

---

## Tech Stack

- **[AWS Strands Agents SDK](https://strandsagents.com/)** — agentic orchestration for both parser and draft generator
- **Amazon Bedrock** — Claude Sonnet 4.6 via cross-region inference profile
- **SQLite** — lightweight persistent store (materials, price_history, review_queue, products)
- **Streamlit** — demo UI
- **Python 3.13**

---

## Project Structure

```
MarginGuard/
├── app.py                    # Streamlit demo UI
├── schema.sql                # SQLite schema
├── marginguard.db            # SQLite database (auto-created)
├── src/
│   ├── parser_agent.py       # Strands Agent: raw text → structured JSON
│   ├── db.py                 # Price upsert, history, margin alert logic
│   └── draft_generator.py    # Strands Agent: alert → draft messages
├── scripts/
│   ├── sql_init.py           # DB initialiser (idempotent)
│   └── demo.py               # CLI demo — full pipeline without Streamlit
└── tests/
    └── test_db.py            # DB logic tests (no mocking)
```

---

## Setup & Running

### Prerequisites

- Python 3.10+
- AWS credentials configured (`aws configure`) with Bedrock access in `us-east-1`
- The inference profile ARN in `src/parser_agent.py` and `src/draft_generator.py` pointing to your account

```bash
pip install strands-agents strands-agents-tools boto3 streamlit
```

### Initialise the database

```bash
python scripts/sql_init.py
```

Expected output:
```
Database initialised at: .../MarginGuard/marginguard.db
Tables: ['materials', 'price_history', 'product_materials', 'products', 'review_queue']
```

### Run the Streamlit UI

```bash
streamlit run app.py
```

Paste a supplier message, click **Process Message**, watch the pipeline run live.

### Run the CLI demo (reliable fallback)

```bash
python scripts/demo.py
```

Runs two built-in messages: first establishes baseline price, second simulates a 33% spike and triggers a margin alert + AI-drafted messages.

```bash
python scripts/demo.py "boss 5 bags rice 600 cedis loading 15"
```

### Run tests

```bash
python tests/test_db.py
```

Expected output:
```
First run alerts: []
Second run alerts: [{'material': 'flour', 'old_price': 150.0, 'new_price': 200, 'pct_change': 33.3, 'is_negotiable': True}]
```

---

## Example: Full Pipeline

**Input:**
> *"boss flour price don go up ooo — 3 bags now 600 cedis, transport 20"*

**Parser output:**
```json
{
  "items": [{
    "material": "flour",
    "quantity": 3,
    "unit": "bag",
    "unit_price": 200.0,
    "total_price": 600,
    "currency": "GHS",
    "surcharges": [{"type": "transport", "amount": 20}],
    "confidence": "high",
    "ambiguity_note": null
  }]
}
```

**Margin alert fires** (GHS 150 → GHS 200, +33.3%)

**Draft — supplier negotiation:**
> *"Hello boss, we have been buying from you for a long time and we appreciate you ooo. Please the 33% increase on flour is very heavy for us. Can we agree on GHS 165 per bag? God bless you."*

**Draft — storefront update:**
> *"Good day valued customers 🙏 Please note our flour-based products have been slightly adjusted due to supplier price increases. We appreciate your continued support!"*

---

## Design Decisions

**Why two separate agents?** The parser needs strict JSON discipline (zero prose); the draft generator needs creative latitude. Separate system prompts and agents prevent them from interfering with each other.

**Why SQLite?** This is a single-artisan tool. SQLite works offline (critical in Ghana where connectivity drops), is zero-config, and the schema already models a full product-material cost structure for future extension.

**Why not hardcode message templates?** Because Ghanaian business relationships are personal — a canned message reads as cold. "Flour went up 33%" should feel different from "cooking gas went up 12%". The AI draft respects that nuance.

---

## Future Work

- [ ] Voice input (many artisans dictate rather than type)
- [ ] Multi-supplier price comparison
- [ ] Product margin calculator (materials → finished goods → selling price)
- [ ] WhatsApp Business API integration (eliminate the paste step)
- [ ] Review queue UI for approving low-confidence extractions

---

## Author

Built for the **AWS Strands Agents SDK Hackathon** · September 2026
