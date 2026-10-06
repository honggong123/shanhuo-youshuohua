"""SQLite 数据层：用户、会话令牌、生成历史。

- 密码使用 PBKDF2-HMAC-SHA256（10 万次迭代）加盐存储；
- 会话令牌为 128 位随机串，存库并可撤销，有效期 7 天；
- 数据库文件 backend/shanhuo.db（已在 .gitignore 中排除）。
"""
import hashlib
import secrets
import sqlite3
import time

from . import config

DB_PATH = config.BACKEND_DIR / "shanhuo.db"

TOKEN_TTL = 7 * 24 * 3600  # 令牌有效期：7 天


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            nickname TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS tokens(
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            poster_url TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL)""")


def _hash(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 100_000
    ).hex()


def _new_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with get_conn() as c:
        c.execute(
            "INSERT INTO tokens(token, user_id, created_at) VALUES(?, ?, ?)",
            (token, user_id, int(time.time())),
        )
    return token


def create_user(username: str, password: str, nickname: str = "") -> dict:
    """注册新用户，成功返回用户信息；校验失败/重名抛 ValueError。"""
    username = username.strip()
    if not 2 <= len(username) <= 20:
        raise ValueError("用户名长度需在 2~20 个字符之间")
    if len(password) < 6:
        raise ValueError("密码至少 6 位")
    nickname = nickname.strip() or username
    salt = secrets.token_hex(16)
    now = int(time.time())
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO users(username, password_hash, salt, nickname, created_at)"
                " VALUES(?, ?, ?, ?, ?)",
                (username, _hash(password, salt), salt, nickname, now),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("该用户名已被注册")
    return {"id": user_id, "username": username, "nickname": nickname}


def verify_login(username: str, password: str) -> tuple[str, dict]:
    """校验账密，成功返回 (token, user)；失败抛 ValueError。"""
    with get_conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if row is None or _hash(password, row["salt"]) != row["password_hash"]:
        raise ValueError("用户名或密码错误")
    user = {"id": row["id"], "username": row["username"], "nickname": row["nickname"]}
    return _new_token(row["id"]), user


def user_from_token(token: str) -> dict | None:
    """根据令牌取当前用户；无效或过期返回 None。"""
    if not token:
        return None
    with get_conn() as c:
        t = c.execute("SELECT * FROM tokens WHERE token = ?", (token,)).fetchone()
        if t is None or int(time.time()) - t["created_at"] > TOKEN_TTL:
            return None
        u = c.execute(
            "SELECT id, username, nickname FROM users WHERE id = ?", (t["user_id"],)
        ).fetchone()
    if u is None:
        return None
    return {"id": u["id"], "username": u["username"], "nickname": u["nickname"]}


def drop_token(token: str) -> None:
    with get_conn() as c:
        c.execute("DELETE FROM tokens WHERE token = ?", (token,))


def add_history(user_id: int, name: str, title: str, poster_url: str) -> dict:
    now = int(time.time())
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO history(user_id, name, title, poster_url, created_at)"
            " VALUES(?, ?, ?, ?, ?)",
            (user_id, name.strip(), title.strip(), poster_url.strip(), now),
        )
        hid = cur.lastrowid
    return {"id": hid, "name": name, "title": title, "poster_url": poster_url, "created_at": now}


def list_history(user_id: int, limit: int = 50) -> list[dict]:
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, name, title, poster_url, created_at FROM history"
            " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_history(user_id: int, history_id: int) -> bool:
    with get_conn() as c:
        cur = c.execute(
            "DELETE FROM history WHERE id = ? AND user_id = ?", (history_id, user_id)
        )
    return cur.rowcount > 0
