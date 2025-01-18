import sqlite3

DB_NAME = "articles.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            publish_date TEXT,
            summary TEXT,
            sentiment_score REAL,
            sentiment_label TEXT
        )
    """)

    conn.commit()
    conn.close()