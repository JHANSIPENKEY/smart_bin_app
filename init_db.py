import sqlite3

conn = sqlite3.connect("waste.db")
cur = conn.cursor()

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    credits INTEGER DEFAULT 0
)
""")

# WASTE STATS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS waste_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waste_type TEXT,
    count INTEGER DEFAULT 0
)
""")

# INSERT INITIAL WASTE TYPES
for wt in ["Plastic", "Organic", "Recyclable", "Non-Recyclable"]:
    cur.execute("""
    INSERT OR IGNORE INTO waste_stats (waste_type, count)
    VALUES (?, 0)
    """, (wt,))

conn.commit()
conn.close()

print("✅ Database initialized successfully!")