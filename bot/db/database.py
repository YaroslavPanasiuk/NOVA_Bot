import asyncpg
from bot.config import DATABASE_NAME

pool: asyncpg.pool.Pool = None

DB_CONFIG = {
    "user": "yaroslav",
    "password": "1246",
    "database": "nova_bot",
    "host": "localhost",
    "port": 5432
}

async def init_db():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)

    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        # Table with telegram_id as PK
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            telegram_id BIGINT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            role TEXT CHECK (role IN ('mentor','participant','pending')) NOT NULL,
            phone_number TEXT,
            instagram TEXT,
            fundraising_goal NUMERIC(12,2),
            photo_url TEXT,
            description TEXT DEFAULT 'no description',
            status TEXT DEFAULT 'pending',
            mentor_id BIGINT REFERENCES bot_users(telegram_id),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)

# Add user after phone verification
async def add_user(phone: str, from_user):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        INSERT INTO bot_users (telegram_id, first_name, last_name, username, phone_number, role)
        VALUES ($1, $2, $3, $4, $5, 'pending')
        ON CONFLICT (telegram_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            username = EXCLUDED.username,
            phone_number = EXCLUDED.phone_number,
            role = 'pending',
            created_at = NOW();
        """, from_user.id, from_user.first_name, from_user.last_name, from_user.username, phone)

# Set role
async def set_role(telegram_id: int, role: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET role=$1
        WHERE telegram_id=$2 AND role='pending';
        """, role, telegram_id)


async def set_photo(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET photo_url=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)


async def set_description(telegram_id: int, description: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET description=$1
        WHERE telegram_id=$2;
        """, description, telegram_id)


async def set_instagram(telegram_id: int, instagram: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET instagram=$1
        WHERE telegram_id=$2;
        """, instagram, telegram_id)


async def set_goal(telegram_id: int, goal: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET fundraising_goal=$1
        WHERE telegram_id=$2;
        """, goal, telegram_id)


async def set_mentor(telegram_id: int, mentor: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET mentor_id=$1
        WHERE telegram_id=$2;
        """, mentor, telegram_id)

# Save mentor profile
async def save_mentor_profile(telegram_id: int, instagram: str, fundraising_goal: float, photo_url: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET instagram=$1, fundraising_goal=$2, photo_url=$3
        WHERE telegram_id=$4 AND role='mentor';
        """, instagram, fundraising_goal, photo_url, telegram_id)

async def update_mentor_status(telegram_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
            UPDATE bot_users
            SET status = $1
            WHERE telegram_id = $2
        """, status, telegram_id)

# Save participant profile
async def save_participant_profile(telegram_id: int, mentor_id: int, instagram: str, fundraising_goal: float, photo_url: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET mentor_id=$1, instagram=$2, fundraising_goal=$3, photo_url=$4
        WHERE telegram_id=$5 AND role='participant';
        """, mentor_id, instagram, fundraising_goal, photo_url, telegram_id)

# Set participant's mentor
async def set_participant_mentor(telegram_id: int, mentor_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET mentor_id=$1
        WHERE telegram_id=$2 AND role='participant';
        """, mentor_id, telegram_id)

# Fetch available mentors
async def get_mentors():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role='mentor'
            ORDER BY created_at
        """)
        return [dict(r) for r in rows]

# Update status
async def set_status(telegram_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET status=$1
        WHERE telegram_id=$2;
        """, status, telegram_id)

# Get all users
async def get_all_users():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            ORDER BY created_at
        """)
        return [dict(r) for r in rows]

# Get pending mentors
async def get_pending_mentors():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role='mentor' AND status='pending'
        """)
        return [dict(r) for r in rows]

# Get user by telegram_id
async def get_user_by_id(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM bot_users WHERE telegram_id=$1", telegram_id)
        return dict(row) if row else None

# Delete user
async def delete_user(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("DELETE FROM bot_users WHERE telegram_id=$1", telegram_id)

# Get n-th approved mentor
async def get_nth_approved_mentor(n: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("""
            SELECT telegram_id
            FROM bot_users
            WHERE role='mentor' AND status='approved'
            ORDER BY telegram_id
            OFFSET $1 LIMIT 1;
        """, n - 1)
        return row["telegram_id"] if row else None


# Fetch all participants of a specific mentor
async def get_participants_of_mentor(mentor_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role = 'participant' AND mentor_id = $1
            ORDER BY created_at
        """, mentor_id)
        return [dict(r) for r in rows]

