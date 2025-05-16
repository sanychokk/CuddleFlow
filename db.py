import aiosqlite
import random
import string

DB_NAME = "bot_data.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                role TEXT,
                name TEXT,
                cycle_length INTEGER DEFAULT 28,
                last_period_date TEXT,
                cravings TEXT,
                partner_id INTEGER,
                invite_code TEXT UNIQUE
            )
        """)
        await db.commit()

async def create_user(tg_id: int, role: str, name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (tg_id, role, name) VALUES (?, ?, ?)
        """, (tg_id, role, name))
        await db.commit()

async def get_user_role(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT role FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_cycle_length(tg_id: int, days: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET cycle_length = ? WHERE tg_id = ?", (days, tg_id))
        await db.commit()

async def get_cycle_length(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT cycle_length FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row[0] if row else 28

async def set_last_period_date(tg_id: int, date_str: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET last_period_date = ? WHERE tg_id = ?", (date_str, tg_id))
        await db.commit()

async def get_last_period_date(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT last_period_date FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_cravings(tg_id: int, text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET cravings = ? WHERE tg_id = ?", (text, tg_id))
        await db.commit()

async def get_cravings(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT cravings FROM users WHERE tg_id = ?", (tg_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def generate_invite_code(tg_id: int):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, что код уникален
        cursor = await db.execute("SELECT tg_id FROM users WHERE invite_code = ?", (code,))
        exists = await cursor.fetchone()
        while exists:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            cursor = await db.execute("SELECT tg_id FROM users WHERE invite_code = ?", (code,))
            exists = await cursor.fetchone()

        await db.execute("UPDATE users SET invite_code = ? WHERE tg_id = ?", (code, tg_id))
        await db.commit()
    return code

async def connect_users_by_code(code: str, tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT tg_id FROM users WHERE invite_code = ?", (code,))
        row = await cursor.fetchone()
        if not row:
            return False
        girl_id = row[0]
        # Связываем друг с другом
        await db.execute("UPDATE users SET partner_id = ? WHERE tg_id = ?", (tg_id, girl_id))
        await db.execute("UPDATE users SET partner_id = ? WHERE tg_id = ?", (girl_id, tg_id))
        await db.commit()
        return True

async def get_reminder_targets():
    async with aiosqlite.connect(DB_NAME) as db:
        # Девушки с партнёрами и датой последнего цикла, которым нужно напомнить (например, если дата не None)
        cursor = await db.execute("""
            SELECT tg_id, partner_id, name FROM users
            WHERE role = 'girl' AND last_period_date IS NOT NULL
        """)
        rows = await cursor.fetchall()
        return rows
