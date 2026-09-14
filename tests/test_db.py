import sys
from pathlib import Path

# Allow running from any directory
ROOT = Path(__file__).resolve().parent.parent   # MarginGuard/
sys.path.insert(0, str(ROOT))

from src.db import process_parsed_items

DB_PATH = str(ROOT / "marginguard.db")

test_json = '{"items": [{"material": "flour", "quantity": 3, "unit": "bag", "unit_price": 150, "total_price": 450, "currency": "GHS", "surcharges": [{"type": "transport", "amount": 20}], "supplier_reference": null, "confidence": "high", "ambiguity_note": null}], "unparsed_fragments": []}'

alerts = process_parsed_items(test_json, db_path=DB_PATH)
print("First run alerts:", alerts)

# Simulate a 33% price spike (150 -> 200)
test_json_2 = test_json.replace('"unit_price": 150', '"unit_price": 200').replace('"total_price": 450', '"total_price": 600')
alerts2 = process_parsed_items(test_json_2, db_path=DB_PATH)
print("Second run alerts:", alerts2)