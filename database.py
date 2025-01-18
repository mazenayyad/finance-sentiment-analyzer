import sqlite3
from datetime import date

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

def fetch_all_articles():
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()

    c.execute("SELECT * FROM articles ORDER BY id DESC")
    rows = c.fetchall() # rows -> each row is a tuple. so list of tuples
    conn.close()

    articles = []
    for row in rows:
        articles.append({
            "id": row[0],
            "title": row[1],
            "publish_date": row[2],
            "summary": row[3],
            "sentiment_score": row[4],
            "sentiment_label": row[5]
        })
    return articles
