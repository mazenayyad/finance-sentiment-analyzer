import sqlite3

DB_NAME = "articles.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source TEXT,
            publish_date TEXT,
            final_url TEXT,
            summary TEXT,
            sentiment_score REAL,
            sentiment_label TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_articles(title, source, publish_date, final_url, summary, sentiment_score, sentiment_label):
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()

    # list columns to fill. VALUES = placeholders
    c.execute("""
        INSERT INTO articles (title, source, publish_date, final_url, summary, sentiment_score, sentiment_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, source, publish_date, final_url, summary, sentiment_score, sentiment_label))

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
            "source": row[2],
            "publish_date": row[3],
            "final_url": row[4],
            "summary": row[5],
            "sentiment_score": row[6],
            "sentiment_label": row[7]
        })
    return articles

def fetch_articles_by_date(day_str):
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()

    c.execute("""
        SELECT * FROM articles
        WHERE publish_date = ?
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
            "publish_date": row[3],
            "final_url": row[4],
            "summary": row[5],
            "sentiment_score": row[6],
            "sentiment_label": row[7]
        })
    return articles

def article_exists(title, source):
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()

    c.execute("""
        SELECT id
        FROM articles
        WHERE title = ? AND source = ?
    """, (title, source))

    row = c.fetchone() # returns None if not found
    conn.close()

    return (row is not None)