import sqlite3
import time
from contextlib import contextmanager
import os

DB_NAME = os.environ.get("DB_PATH", "words.db")

ALLOWED_INTERVALS = {30, 60, 120, 1440}  # 30 мин / 1 час / 2 часа / сутки


@contextmanager
def get_conn():
    """Единая точка открытия соединения"""
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with open("models.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())


def get_or_create_user(telegram_id: int) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,))
        return c.lastrowid


def set_active(user_id: int, is_active: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, user_id),
        )

def set_interval(user_id: int, minutes: int):
    if minutes not in ALLOWED_INTERVALS:
        raise ValueError(f"Недопустимый интервал: {minutes}")
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET interval_minutes = ? WHERE id = ?",
            (minutes, user_id),
        )

def get_user(user_id: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, telegram_id, is_active, interval_minutes, last_sent_at "
            "FROM users WHERE id = ?",
            (user_id,),
        )
        row = c.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "telegram_id": row[1],
        "is_active": bool(row[2]),
        "interval_minutes": row[3],
        "last_sent_at": row[4],
    }


def get_due_active_users():
    """
    Возвращает активных пользователей, которым пора отправить слово
    (прошло >= interval_minutes с последней отправки)
    """
    now = int(time.time())
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, telegram_id, interval_minutes, last_sent_at "
            "FROM users WHERE is_active = 1"
        )
        rows = c.fetchall()

    due = []
    for user_id, telegram_id, interval_minutes, last_sent_at in rows:
        if now - last_sent_at >= interval_minutes * 60:
            due.append({
                "id": user_id,
                "telegram_id": telegram_id,
                "interval_minutes": interval_minutes,
                "last_sent_at": last_sent_at,
            })
    return due


def update_last_sent(user_id: int, timestamp: int = None):
    timestamp = timestamp or int(time.time())
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET last_sent_at = ? WHERE id = ?",
            (timestamp, user_id),
        )


def get_random_word():
    """Возвращает случайное слово из базы или None, если база пустая"""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, word, plural, translation FROM words "
            "ORDER BY RANDOM() LIMIT 1"
        )
        row = c.fetchone()
    if not row:
        return None
    return {"id": row[0], "word": row[1], "plural": row[2], "translation": row[3]}


def add_word(word: str, translation: str, plural: str = None) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO words (word, plural, translation) VALUES (?, ?, ?)",
            (word, plural, translation),
        )
        return c.lastrowid


def count_words() -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM words")
        return c.fetchone()[0]


def get_current_word():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT word_id, word, plural, translation, sentence_de, sentence_ru, generated_at "
            "FROM current_word WHERE id = 1"
        )
        row = c.fetchone()
    if not row:
        return None
    return {
        "word_id": row[0],
        "word": row[1],
        "plural": row[2],
        "translation": row[3],
        "sentence_de": row[4],
        "sentence_ru": row[5],
        "generated_at": row[6],
    }


def set_current_word(word_id, word, plural, translation, sentence_de, sentence_ru):
    now = int(time.time())
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO current_word (id, word_id, word, plural, translation, sentence_de, sentence_ru, generated_at)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                word_id=excluded.word_id,
                word=excluded.word,
                plural=excluded.plural,
                translation=excluded.translation,
                sentence_de=excluded.sentence_de,
                sentence_ru=excluded.sentence_ru,
                generated_at=excluded.generated_at
            """,
            (word_id, word, plural, translation, sentence_de, sentence_ru, now),
        )


def record_sent_message(user_id: int, message_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sent_messages (user_id, message_id, sent_at) VALUES (?, ?, ?)",
            (user_id, message_id, int(time.time())),
        )


def pop_old_messages(user_id: int, keep: int = 3):
    """
    Оставляет в таблице только 'keep' самых свежих сообщений пользователя,
    остальные удаляет из БД и возвращает их message_id — чтобы вызывающий код
    удалил их и из самого чата в Telegram
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, message_id FROM sent_messages WHERE user_id = ? ORDER BY sent_at DESC, id DESC",
            (user_id,),
        )
        rows = c.fetchall()
        old_rows = rows[keep:]
        if old_rows:
            conn.executemany(
                "DELETE FROM sent_messages WHERE id = ?",
                [(row_id,) for row_id, _ in old_rows],
            )
    return [message_id for _, message_id in old_rows]