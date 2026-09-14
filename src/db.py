import sqlite3
import json
from pathlib import Path
from datetime import datetime

_DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "marginguard.db")

def process_parsed_items(parsed_json_str, db_path=None):
    """
    Takes the raw JSON string output from the MarginGuard parser agent,
    routes each item by confidence, and returns any margin alerts triggered.
    """
    if db_path is None:
        db_path = _DEFAULT_DB
    data = json.loads(parsed_json_str)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    alerts = []
    now = datetime.utcnow().isoformat()

    for item in data.get("items", []):
        if item["confidence"] == "low":
            cur.execute(
                """INSERT INTO review_queue
                   (raw_material_text, parsed_json, ambiguity_note, received_at)
                   VALUES (?, ?, ?, ?)""",
                (item.get("material"), json.dumps(item), item.get("ambiguity_note"), now)
            )
            continue

        # medium/high confidence — needs at least a unit_price to be useful
        unit_price = item.get("unit_price")
        if unit_price is None and item.get("total_price") and item.get("quantity"):
            unit_price = item["total_price"] / item["quantity"]

        if unit_price is None:
            # still not enough to act on — treat like review queue
            cur.execute(
                """INSERT INTO review_queue
                   (raw_material_text, parsed_json, ambiguity_note, received_at)
                   VALUES (?, ?, ?, ?)""",
                (item.get("material"), json.dumps(item), "Could not resolve unit_price", now)
            )
            continue

        material_name = item["material"]
        cur.execute("SELECT id, current_unit_price, is_negotiable FROM materials WHERE name = ?", (material_name,))
        row = cur.fetchone()

        if row is None:
            # first time seeing this material
            cur.execute(
                """INSERT INTO materials (name, unit, current_unit_price, last_updated)
                   VALUES (?, ?, ?, ?)""",
                (material_name, item.get("unit"), unit_price, now)
            )
            material_id = cur.lastrowid
            old_price = None
            is_negotiable = 1
        else:
            material_id, old_price, is_negotiable = row
            cur.execute(
                "UPDATE materials SET current_unit_price = ?, last_updated = ? WHERE id = ?",
                (unit_price, now, material_id)
            )

        cur.execute(
            """INSERT INTO price_history
               (material_id, quantity, unit_price, total_price, surcharges_json,
                supplier_reference, confidence, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (material_id, item.get("quantity"), unit_price, item.get("total_price"),
             json.dumps(item.get("surcharges", [])), item.get("supplier_reference"),
             item["confidence"], now)
        )

        # margin check — only meaningful if we had a previous price
        if old_price and old_price > 0:
            pct_change = ((unit_price - old_price) / old_price) * 100
            if pct_change >= 10:  # threshold, tune as needed
                alerts.append({
                    "material": material_name,
                    "old_price": old_price,
                    "new_price": unit_price,
                    "pct_change": round(pct_change, 1),
                    "is_negotiable": bool(is_negotiable)
                })

    conn.commit()
    conn.close()
    return alerts