"""
MarginGuard — Streamlit demo UI
Run: streamlit run app.py
"""

import streamlit as st
import sqlite3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.parser_agent import parse_message
from src.db import process_parsed_items, _DEFAULT_DB
from src.draft_generator import generate_drafts

st.set_page_config(page_title="MarginGuard", page_icon="📊", layout="centered")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📊 MarginGuard")
st.caption("AI margin tracker for Ghanaian artisans — paste a supplier message, see your margins move in real time.")

st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
st.subheader("📩 Paste Supplier Message")
sample = "boss send 3 bags flour 450 cedis, transport extra 20"
user_input = st.text_area(
    "Supplier message (WhatsApp, SMS, voice-to-text):",
    value=sample,
    height=100,
    placeholder="e.g. 'boss send 3 bags flour 450 cedis, transport extra 20'",
)

process_btn = st.button("⚙️ Process Message", type="primary", use_container_width=True)

# ── Processing ────────────────────────────────────────────────────────────────
if process_btn and user_input.strip():
    with st.spinner("Parsing message with AI…"):
        try:
            parsed_str = parse_message(user_input.strip())
        except Exception as e:
            st.error(f"❌ Parser error: {e}")
            st.stop()

    st.divider()
    st.subheader("🔍 Parsed Items")
    try:
        parsed_data = json.loads(parsed_str)
        st.json(parsed_data)
    except json.JSONDecodeError:
        st.warning("⚠️ Could not parse JSON from model response — raw output:")
        st.code(parsed_str)
        st.stop()

    # ── DB + alerts ──────────────────────────────────────────────────────────
    with st.spinner("Updating price history & checking margins…"):
        try:
            alerts = process_parsed_items(parsed_str)
        except Exception as e:
            st.error(f"❌ DB error: {e}")
            st.stop()

    if alerts:
        st.divider()
        st.subheader("🚨 Margin Alerts")
        for alert in alerts:
            pct = alert["pct_change"]
            colour = "🔴" if pct >= 20 else "🟠"
            st.warning(
                f"{colour} **{alert['material'].title()}** jumped "
                f"GHS {alert['old_price']:.2f} → GHS {alert['new_price']:.2f} "
                f"(**+{pct}%**)"
            )

            # ── Draft messages ───────────────────────────────────────────────
            with st.spinner(f"Generating draft messages for {alert['material']}…"):
                try:
                    drafts = generate_drafts(alert)
                except Exception as e:
                    st.error(f"❌ Draft generation error: {e}")
                    drafts = {}

            if drafts:
                st.subheader("✍️ Suggested Drafts")
                if "negotiation_message" in drafts:
                    st.markdown("**📞 Supplier Negotiation Message:**")
                    st.markdown(f"> {drafts['negotiation_message']}")
                if "storefront_caption" in drafts:
                    st.markdown("**🏪 Storefront / WhatsApp Status Update:**")
                    st.markdown(f"> {drafts['storefront_caption']}")
                if "customer_notice" in drafts:
                    st.markdown("**📢 Customer Price Notice:**")
                    st.markdown(f"> {drafts['customer_notice']}")
    else:
        st.success("✅ Prices recorded — no significant margin change detected.")

# ── Materials Table ───────────────────────────────────────────────────────────
st.divider()
st.subheader("📦 Materials Price Tracker")
st.caption("Live view of all tracked materials and their current prices.")

try:
    conn = sqlite3.connect(_DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT name, unit, current_unit_price, last_updated FROM materials ORDER BY last_updated DESC"
    )
    rows = cur.fetchall()
    conn.close()

    if rows:
        table_data = [
            {
                "Material": r["name"].title(),
                "Unit": r["unit"] or "—",
                "Current Price (GHS)": f"{r['current_unit_price']:.2f}" if r["current_unit_price"] else "—",
                "Last Updated": r["last_updated"][:19].replace("T", " ") if r["last_updated"] else "—",
            }
            for r in rows
        ]
        st.table(table_data)
    else:
        st.info("No materials tracked yet — process your first message above.")
except Exception as e:
    st.error(f"Could not load materials table: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("MarginGuard · Built with AWS Strands Agents SDK + Amazon Bedrock · Demo")
