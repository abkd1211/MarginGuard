-- materials: current known state of each input the artisan buys
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- e.g. "flour"
    unit TEXT,                       -- e.g. "bag"
    current_unit_price REAL,         -- latest confirmed unit price, GHS
    is_negotiable INTEGER DEFAULT 1, -- 1 = market price, 0 = govt/regulated
    last_updated TEXT                -- ISO timestamp
);

-- price_history: every parsed price event, high/medium confidence only
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER REFERENCES materials(id),
    quantity REAL,
    unit_price REAL,
    total_price REAL,
    surcharges_json TEXT,            -- store the surcharges array as JSON text
    supplier_reference TEXT,
    confidence TEXT,
    recorded_at TEXT                 -- ISO timestamp
);

-- review_queue: low-confidence items, held for human confirmation
CREATE TABLE review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_material_text TEXT,          -- material name as extracted, unmatched
    parsed_json TEXT,                -- full parser output for this item
    ambiguity_note TEXT,
    received_at TEXT,
    resolved INTEGER DEFAULT 0
);

-- products: what the artisan sells, and what it's made of
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- e.g. "Dress"
    selling_price REAL
);

CREATE TABLE product_materials (
    product_id INTEGER REFERENCES products(id),
    material_id INTEGER REFERENCES materials(id),
    quantity_used REAL,              -- how much of this material per product
    PRIMARY KEY (product_id, material_id)
);