import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source TEXT,
            pub_date TEXT,
            final_url TEXT,
            summary TEXT,
            sentiment_score REAL,
            sentiment_label TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS finance_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_str TEXT NOT NULL UNIQUE,
            avg_sentiment REAL,
            btc_price REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_articles(title, source, pub_date, final_url, summary, sentiment_score, sentiment_label):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    # list columns to fill. VALUES = placeholders
    c.execute("""
        INSERT INTO articles (title, source, pub_date, final_url, summary, sentiment_score, sentiment_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, source, pub_date, final_url, summary, sentiment_score, sentiment_label))

    conn.commit()
    conn.close()

def fetch_all_articles():
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("SELECT * FROM articles ORDER BY id DESC")
    rows = c.fetchall() # rows -> each row is a tuple. so list of tuples
    conn.close()

    articles = []
    for row in rows:
        articles.append({
            "id": row[0],
            "title": row[1],
            "source": row[2],
            "pub_date": row[3],
            "final_url": row[4],
            "summary": row[5],
            "sentiment_score": row[6],
            "sentiment_label": row[7]
        })
    return articles

def fetch_articles_by_date(day_str):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("""
        SELECT * FROM articles
        WHERE pub_date = ?
        ORDER BY id DESC
    """, (day_str,)) # (day_str,) is a tuple containing 1 element: day_str
    rows = c.fetchall() # rows -> each row is a tuple. so list of tuples
    conn.close()
    
    # convert each tuple to a dict
    articles = []
    for row in rows:
        articles.append({
            "id": row[0],
            "title": row[1],
            "source": row[2],
            "pub_date": row[3],
            "final_url": row[4],
            "summary": row[5],
            "sentiment_score": row[6],
            "sentiment_label": row[7]
        })
    return articles

def article_exists(title, source):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("""
        SELECT id
        FROM articles
        WHERE title = ? AND source = ?
    """, (title, source))

    row = c.fetchone() # returns None if not found
    conn.close()

    return (row is not None)

def store_daily_aggregate(date_str, avg_sentiment, btc_price):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO finance_daily (date_str, avg_sentiment, btc_price)
        VALUES (?, ?, ?)
    """, (date_str, avg_sentiment, btc_price))

    conn.commit()
    conn.close()

def fetch_finance_daily(limit_days=30):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()

    c.execute("""
        SELECT date_str, avg_sentiment, btc_price
        FROM finance_daily
        ORDER BY date_str DESC
        LIMIT ?
    """, (limit_days,))

    rows = c.fetchall()
    conn.close()

    # rows will be from newest to oldest. so we reverse them to get oldest -> newest
    rows.reverse()

    data = []
    for row in rows:
        data.append({
            "date_str": row[0],
            "avg_sentiment": row[1],
            "btc_price": row[2]
        })
    return data