import os
import json
import sqlite3
from datetime import datetime

DB_PATH = "data/cursed.db"
CARDS_DIR = "data/cards"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(CARDS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Schema updated to match the Context-Aware PRD
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection (
            id TEXT PRIMARY KEY,
            subject TEXT,
            name TEXT,
            class TEXT,
            rarity TEXT,
            stats TEXT,
            quirky_text TEXT,
            lore TEXT,
            image_path TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_card(card_id: str, metadata: dict, rarity: str, stats: dict, image_path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO collection (id, subject, name, class, rarity, stats, quirky_text, lore, image_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        card_id,
        metadata.get("subject", "Unknown"),
        metadata.get("name", "Null Anomaly"),
        metadata.get("class", "GLITCH"),
        rarity,
        json.dumps(stats),
        metadata.get("quirky_text", "Error 404: Vibe not found."),
        metadata.get("lore", "Data corrupted."),
        image_path,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_collection() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM collection ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    cards = []
    for row in rows:
        card = dict(row)
        try:
            card["stats"] = json.loads(card["stats"])
        except (TypeError, json.JSONDecodeError):
            card["stats"] = {}
        cards.append(card)
    return cards
