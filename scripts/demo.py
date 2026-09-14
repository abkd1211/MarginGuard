"""
demo.py — MarginGuard CLI demo fallback

Runs the full pipeline without Streamlit:
  parser_agent → db.process_parsed_items → draft_generator

Usage:
    python scripts/demo.py
    python scripts/demo.py "boss 5 bags rice 600 cedis, loading 15"

If no message is supplied, runs through two built-in demo messages that
show the margin spike detection and draft generation in action.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.parser_agent import parse_message
from src.db import process_parsed_items
from src.draft_generator import generate_drafts

DIVIDER = "─" * 60

DEMO_MESSAGES = [
    "boss send 3 bags flour 450 cedis, transport extra 20",
    "boss flour price don go up ooo — 3 bags now 600 cedis, transport 20",
]


def run_pipeline(message: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"📩 INPUT: {message}")
    print(DIVIDER)

    # ── Step 1: Parse ─────────────────────────────────────────────────────────
    print("⚙️  Parsing with AI agent…")
    try:
        raw = parse_message(message)
    except Exception as e:
        print(f"❌ Parser error: {e}")
        return

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print("❌ Could not parse JSON from model — raw output:")
        print(raw)
        return

    print("🔍 Parsed items:")
    print(json.dumps(parsed, indent=2))

    # ── Step 2: Update DB + check margins ────────────────────────────────────
    print("\n💾 Updating price history…")
    alerts = process_parsed_items(raw)

    if not alerts:
        print("✅ No significant margin change detected (or first-time entry).")
        return

    for alert in alerts:
        print(f"\n🚨 MARGIN ALERT: {alert['material'].upper()}")
        print(f"   Old price : GHS {alert['old_price']:.2f}")
        print(f"   New price : GHS {alert['new_price']:.2f}")
        print(f"   Change    : +{alert['pct_change']}%")
        print(f"   Negotiable: {alert['is_negotiable']}")

        # ── Step 3: Generate drafts ───────────────────────────────────────────
        print("\n✍️  Generating draft messages…")
        try:
            drafts = generate_drafts(alert)
        except Exception as e:
            print(f"❌ Draft generation error: {e}")
            continue

        if "negotiation_message" in drafts:
            print("\n📞 Supplier Negotiation Message:")
            print(f"   {drafts['negotiation_message']}")
        if "storefront_caption" in drafts:
            print("\n🏪 Storefront / WhatsApp Status:")
            print(f"   {drafts['storefront_caption']}")
        if "customer_notice" in drafts:
            print("\n📢 Customer Price Notice:")
            print(f"   {drafts['customer_notice']}")


def show_materials_table() -> None:
    import sqlite3
    from src.db import _DEFAULT_DB

    print(f"\n{DIVIDER}")
    print("📦 MATERIALS TABLE (current state)")
    print(DIVIDER)

    conn = sqlite3.connect(_DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name, unit, current_unit_price, last_updated FROM materials ORDER BY last_updated DESC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("(no materials tracked yet)")
        return

    print(f"{'Material':<20} {'Unit':<10} {'Price (GHS)':<14} {'Last Updated'}")
    print("─" * 65)
    for r in rows:
        ts = (r["last_updated"] or "")[:19].replace("T", " ")
        price = f"{r['current_unit_price']:.2f}" if r["current_unit_price"] else "—"
        print(f"{r['name'].title():<20} {(r['unit'] or '—'):<10} {price:<14} {ts}")


if __name__ == "__main__":
    messages = sys.argv[1:] if len(sys.argv) > 1 else DEMO_MESSAGES

    for msg in messages:
        run_pipeline(msg)

    show_materials_table()
    print(f"\n{DIVIDER}")
    print("✅ Demo complete.")
