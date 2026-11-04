# All SQL for users lives here.
from app import database
from app.core.security import hash_password
from app.schemas.user import UserCreate

PUBLIC_COLUMNS = "id, username, full_name, role, created_at"


async def count_users() -> int:
    return await database.pool.fetchval("SELECT count(*) FROM users")


async def get_user_by_username(username: str, include_password: bool = False):
    columns = PUBLIC_COLUMNS + (", hashed_password" if include_password else "")
    row = await database.pool.fetchrow(
        f"SELECT {columns} FROM users WHERE username = $1", username
    )
    return dict(row) if row else None


async def get_all_users():
    rows = await database.pool.fetch(f"SELECT {PUBLIC_COLUMNS} FROM users ORDER BY id")
    return [dict(row) for row in rows]


async def create_user(user: UserCreate, role: str):
    query = f"""
INSERT INTO users (username, full_name, hashed_password, role)
VALUES ($1, $2, $3, $4)
RETURNING {PUBLIC_COLUMNS}
"""
    row = await database.pool.fetchrow(
        query, user.username, user.full_name, hash_password(user.password), role
    )
    return dict(row)


async def delete_user(user_id: int):
    row = await database.pool.fetchrow(
        f"DELETE FROM users WHERE id = $1 RETURNING {PUBLIC_COLUMNS}", user_id
    )
    return dict(row) if row else None
