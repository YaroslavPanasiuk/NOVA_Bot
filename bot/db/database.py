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
            default_name TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            role TEXT CHECK (role IN ('mentor','participant','pending')) NOT NULL,
            phone_number TEXT DEFAULT '',
            instagram TEXT DEFAULT '',
            fundraising_goal NUMERIC(12,2) DEFAULT 0,
            jar_url TEXT DEFAULT '',
            description TEXT DEFAULT 'no description',
            status TEXT DEFAULT 'pending',
            mentor_id BIGINT REFERENCES bot_users(telegram_id),
            design_preference TEXT DEFAULT '',
            photo_compressed TEXT,
            photo_uncompressed TEXT,
            design_compressed TEXT,
            design_uncompressed TEXT,
            design_video TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_questions (
            id SERIAL PRIMARY KEY,         -- unique ID for each question
            telegram_id BIGINT REFERENCES bot_users(telegram_id) ON DELETE CASCADE,
            question_text TEXT NOT NULL DEFAULT '',
            status TEXT DEFAULT 'not answered',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            name TEXT UNIQUE PRIMARY KEY,
            type TEXT CHECK (type IN ('video','animation','photo_compressed', 'photo_uncompressed', 'design_compressed', 'design_uncompressed')),
            file_id TEXT,
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
        WHERE telegram_id=$2;
        """, role, telegram_id)


async def set_uncompressed_photo(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute(f"""
        UPDATE bot_users
        SET photo_uncompressed=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)


async def set_compressed_photo(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute(f"""
        UPDATE bot_users
        SET photo_compressed=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)


async def set_compressed_design(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute(f"""
        UPDATE bot_users
        SET design_compressed=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)


async def set_uncompressed_design(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute(f"""
        UPDATE bot_users
        SET design_uncompressed=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)


async def set_design_video(telegram_id: int, file_id: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute(f"""
        UPDATE bot_users
        SET design_video=$1
        WHERE telegram_id=$2;
        """, file_id, telegram_id)



async def set_default_name(telegram_id: int, name: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET default_name=$1
        WHERE telegram_id=$2;
        """, name, telegram_id)


async def set_jar(telegram_id: int, jar_url: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET jar_url=$1
        WHERE telegram_id=$2;
        """, jar_url, telegram_id)


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


async def set_design_preference(telegram_id: int, design_preference: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET design_preference=$1
        WHERE telegram_id=$2;
        """, design_preference, telegram_id)


async def set_goal(telegram_id: int, goal: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET fundraising_goal=$1
        WHERE telegram_id=$2;
        """, goal, telegram_id)


async def update_created_at(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET created_at=NOW()
        WHERE telegram_id=$1;
        """, telegram_id)


async def set_mentor(telegram_id: int, mentor: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET mentor_id=$1
        WHERE telegram_id=$2;
        """, mentor, telegram_id)

# Save mentor profile
async def save_mentor_profile(telegram_id: int, instagram: str, fundraising_goal: float):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET instagram=$1, fundraising_goal=$2
        WHERE telegram_id=$3 AND role='mentor';
        """, instagram, fundraising_goal, telegram_id)

async def update_status(telegram_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
            UPDATE bot_users
            SET status = $1
            WHERE telegram_id = $2;
        """, status, telegram_id)

# Save participant profile
async def save_participant_profile(telegram_id: int, mentor_id: int, instagram: str, fundraising_goal: float):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE bot_users
        SET mentor_id=$1, instagram=$2, fundraising_goal=$3
        WHERE telegram_id=$4 AND role='participant';
        """, mentor_id, instagram, fundraising_goal, telegram_id)

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

# Fetch approved mentors
async def get_approved_mentors():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role='mentor' AND status='approved'
            ORDER BY created_at;
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

# Get all users
async def get_users_with_no_design():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE design_uncompressed IS NULL
            ORDER BY created_at;
        """)
        return [dict(r) for r in rows]

# Get pending mentors
async def get_pending_mentors():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role='mentor' AND status='pending';
        """)
        return [dict(r) for r in rows]

# Get pending participants
async def get_pending_participants(mentor_id):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT *
            FROM bot_users
            WHERE role='participant' AND status='pending' AND mentor_id=$1
            ORDER BY created_at;
        """, mentor_id)
        return [dict(r) for r in rows]

# Get user by telegram_id
async def get_user_by_id(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM bot_users WHERE telegram_id=$1", telegram_id)
        return dict(row) if row else None

# Get user by telegram_id
async def get_user_by_username(username: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM bot_users WHERE username=$1", username)
        return dict(row) if row else None

# Delete user
async def delete_user(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("DELETE FROM bot_users WHERE telegram_id=$1", telegram_id)

async def force_delete_user(telegram_id: int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("DELETE FROM bot_users WHERE mentor_id=$1", telegram_id)
        await conn.execute("DELETE FROM user_questions WHERE telegram_id=$1", telegram_id)
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
            WHERE role = 'participant' AND mentor_id = $1 AND status = 'approved'
            ORDER BY created_at
        """, mentor_id)
        return [dict(r) for r in rows]
    

async def add_question(telegram_id: int, question_text: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
            INSERT INTO user_questions (telegram_id, question_text)
            VALUES ($1, $2);
        """, telegram_id, question_text)


async def get_questions():
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        rows = await conn.fetch("""
            SELECT * FROM user_questions
            ORDER BY created_at DESC;
        """)
        return [dict(r) for r in rows]


async def get_question_by_id(id:int):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM user_questions WHERE id=$1", id)
        return dict(row) if row else None
    

async def set_question_status(id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
        UPDATE user_questions
        SET status=$1
        WHERE id=$2;
        """, status, id)
    

async def add_file(file_id: int, type: str, name=""):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        await conn.execute("""
            INSERT INTO files (file_id, type, name)
            VALUES ($1, $2, $3)
            ON CONFLICT (name) DO UPDATE SET
                type = EXCLUDED.type,
                name = EXCLUDED.name,
                file_id = EXCLUDED.file_id;
            """, file_id, type, name)


async def get_file_by_id(id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM files WHERE file_id=$1", id)
        return dict(row) if row else None


async def get_file_by_name(name:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT * FROM files WHERE name=$1", name)
        return dict(row) if row else None


async def get_user_compressed_photo(user_id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT photo_compressed FROM bot_users WHERE telegram_id=$1", user_id)
        return row['photo_compressed'] if row else None


async def get_user_uncompressed_photo(user_id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT photo_uncompressed FROM bot_users WHERE telegram_id=$1", user_id)
        return row['photo_uncompressed'] if row else None


async def get_user_compressed_design(user_id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT design_compressed FROM bot_users WHERE telegram_id=$1", user_id)
        return row['design_compressed'] if row else None


async def get_user_uncompressed_design(user_id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT design_uncompressed FROM bot_users WHERE telegram_id=$1", user_id)
        return row['design_uncompressed'] if row else None


async def get_user_design_video(user_id:str):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {DATABASE_NAME};")
        row = await conn.fetchrow("SELECT design_video FROM bot_users WHERE telegram_id=$1", user_id)
        return row['design_video'] if row else None

