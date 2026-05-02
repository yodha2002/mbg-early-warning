"""
database.py — Handler Database
Mendukung dua mode:
  - SQLite : untuk development lokal (otomatis jika tidak ada SUPABASE_URL)
  - Supabase: untuk deployment Streamlit Cloud (set SUPABASE_URL & SUPABASE_KEY di .env)
"""

import os
import sqlite3
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Deteksi mode database ────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

DB_PATH = os.getenv("SQLITE_PATH", "mbg_warning.db")

_supabase_client = None

if USE_SUPABASE:
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Database mode: Supabase (cloud)")
    except ImportError:
        logger.warning("supabase-py tidak terinstall. Fallback ke SQLite.")
        USE_SUPABASE = False
else:
    logger.info("Database mode: SQLite (lokal)")


# ─── SQL schema Supabase (jalankan sekali di Supabase SQL Editor) ─────────────
SUPABASE_SCHEMA = """
-- Jalankan ini di Supabase → SQL Editor sekali saja
CREATE TABLE IF NOT EXISTS articles (
  id          BIGSERIAL PRIMARY KEY,
  source      TEXT NOT NULL,
  title       TEXT UNIQUE NOT NULL,
  url         TEXT,
  published_date TEXT,
  content     TEXT,
  score       INTEGER DEFAULT 0,
  risk_level  TEXT DEFAULT 'Hijau',
  province    TEXT DEFAULT '',
  victim_count INTEGER DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

# ─── SQLite: inisialisasi ──────────────────────────────────────────────────────
def init_db():
    """Buat tabel SQLite (hanya dipakai di mode lokal)."""
    if USE_SUPABASE:
        logger.info("Supabase mode: skip init_db() lokal.")
        print(f"  INFO: Pastikan tabel 'articles' sudah dibuat di Supabase.\n"
              f"  Gunakan SQL berikut:\n{SUPABASE_SCHEMA}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            source       TEXT NOT NULL,
            title        TEXT UNIQUE NOT NULL,
            url          TEXT,
            published_date TEXT,
            content      TEXT,
            score        INTEGER DEFAULT 0,
            risk_level   TEXT DEFAULT 'Hijau',
            province     TEXT DEFAULT '',
            victim_count INTEGER DEFAULT 0,
            created_at   TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"SQLite DB siap: {DB_PATH}")


# ─── Simpan artikel ───────────────────────────────────────────────────────────
def save_articles(articles: list[dict]) -> int:
    """
    Simpan artikel baru ke database. Artikel duplikat (title sama) di-skip.
    Return: jumlah artikel yang berhasil disimpan.
    """
    saved = 0
    now = datetime.now().isoformat()

    if USE_SUPABASE:
        for a in articles:
            try:
                payload = {
                    "source":         a.get("source", ""),
                    "title":          a.get("title", "").strip(),
                    "url":            a.get("url", ""),
                    "published_date": a.get("published_date", ""),
                    "content":        a.get("content", ""),
                    "created_at":     now,
                }
                if not payload["title"]:
                    continue
                # upsert: insert atau update jika title sudah ada
                _supabase_client.table("articles").upsert(
                    payload, on_conflict="title"
                ).execute()
                saved += 1
            except Exception as e:
                logger.error(f"  Supabase save error: {e}")
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for a in articles:
            title = a.get("title", "").strip()
            if not title:
                continue
            try:
                c.execute("""
                    INSERT OR IGNORE INTO articles
                        (source, title, url, published_date, content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    a.get("source", ""),
                    title,
                    a.get("url", ""),
                    a.get("published_date", ""),
                    a.get("content", ""),
                    now,
                ))
                if c.rowcount > 0:
                    saved += 1
            except Exception as e:
                logger.error(f"  SQLite save error: {e}")
        conn.commit()
        conn.close()

    logger.info(f"Tersimpan: {saved}/{len(articles)} artikel baru")
    return saved


# ─── Ambil semua artikel ──────────────────────────────────────────────────────
def get_all_articles() -> list[dict]:
    """Ambil semua artikel dari database, urut terbaru dulu."""
    if USE_SUPABASE:
        try:
            res = (
                _supabase_client
                .table("articles")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return res.data
        except Exception as e:
            logger.error(f"Supabase fetch error: {e}")
            return []
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM articles ORDER BY created_at DESC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"SQLite fetch error: {e}")
            return []


# ─── Update skor & metadata ───────────────────────────────────────────────────
def update_article_score(article_id, score: int, risk_level: str,
                          province: str, victim_count: int):
    """Update kolom score, risk_level, province, victim_count berdasarkan id."""
    payload = {
        "score":        score,
        "risk_level":   risk_level,
        "province":     province,
        "victim_count": victim_count,
    }
    if USE_SUPABASE:
        try:
            _supabase_client.table("articles").update(payload).eq("id", article_id).execute()
        except Exception as e:
            logger.error(f"Supabase update error (id={article_id}): {e}")
    else:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""
                UPDATE articles
                SET score=?, risk_level=?, province=?, victim_count=?
                WHERE id=?
            """, (score, risk_level, province, victim_count, article_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SQLite update error (id={article_id}): {e}")


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    test = [{
        "source": "Test",
        "title": f"[TEST] Artikel uji coba {datetime.now().isoformat()}",
        "url": "https://example.com",
        "published_date": "2025-01-01",
        "content": "Ini artikel uji coba sistem early warning.",
    }]
    n = save_articles(test)
    print(f"Tersimpan: {n}")
    data = get_all_articles()
    print(f"Total artikel di DB: {len(data)}")
