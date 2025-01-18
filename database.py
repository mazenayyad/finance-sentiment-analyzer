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

def insert_articles(title, publish_date, summary, sentiment_score, sentiment_label):
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()

    # list columns to fill. VALUES = placeholders
    c.execute("""
        INSERT INTO articles (title, publish_date, summary, sentiment_score, sentiment_label)
        VALUES (?, ?, ?, ?, ?)
    """, (title, publish_date, summary, sentiment_score, sentiment_label))

    conn.commit()
    conn.close()
