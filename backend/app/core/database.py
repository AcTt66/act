from __future__ import annotations

import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import SETTINGS


DB_CONFIG = SETTINGS.get("database", {})
DB_TYPE = str(DB_CONFIG.get("type", "sqlite")).lower()
USE_POSTGRES = DB_TYPE in {"postgres", "postgresql"}
DB_PATH = Path(DB_CONFIG.get("sqlite_path", "../data/runtime/medix_enterprise.db"))
POSTGRES_URL = str(DB_CONFIG.get("postgres_url", ""))


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _convert_placeholders(sql: str) -> str:
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def _ph(count: int) -> str:
    token = "%s" if USE_POSTGRES else "?"
    return ",".join(token for _ in range(count))


def get_conn():
    if USE_POSTGRES:
        if not POSTGRES_URL:
            raise RuntimeError("database.postgres_url is empty")
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(POSTGRES_URL, row_factory=dict_row, connect_timeout=5)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(conn, sql: str, params: tuple | list = ()):
    return conn.execute(_convert_placeholders(sql), params)


def _row_to_dict(row: Any) -> Dict[str, Any]:
    return dict(row) if row is not None else {}


def init_db() -> None:
    with get_conn() as conn:
        if USE_POSTGRES:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    id_number TEXT,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    created_at TEXT,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    scene TEXT,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS encounters (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT,
                    user_id TEXT,
                    scene TEXT,
                    chief_complaint TEXT,
                    risk_level TEXT,
                    department TEXT,
                    summary TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT,
                    department TEXT,
                    doctor TEXT,
                    doctor_title TEXT,
                    visit_date TEXT,
                    period TEXT,
                    time_slot TEXT,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_attachments (
                    id BIGSERIAL PRIMARY KEY,
                    message_id BIGINT NOT NULL,
                    doc_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    position INTEGER DEFAULT 0,
                    created_at TEXT
                )
                """
            )
        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    id_number TEXT,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    created_at TEXT,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    scene TEXT,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS encounters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id TEXT,
                    scene TEXT,
                    chief_complaint TEXT,
                    risk_level TEXT,
                    department TEXT,
                    summary TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    department TEXT,
                    doctor TEXT,
                    doctor_title TEXT,
                    visit_date TEXT,
                    period TEXT,
                    time_slot TEXT,
                    status TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    doc_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    position INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages(id),
                    FOREIGN KEY (doc_id) REFERENCES medical_documents(doc_id)
                )
                """
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health_profiles (
                user_id TEXT PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                chronic_diseases TEXT,
                allergy_history TEXT,
                medication_history TEXT,
                address TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS medical_documents (
                doc_id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT,
                file_name TEXT,
                file_path TEXT,
                doc_type TEXT,
                title TEXT,
                summary TEXT,
                parsed_json TEXT,
                confidence REAL,
                page_count INTEGER,
                created_at TEXT
            )
            """
        )
        conn.commit()

        # 数据库迁移：添加新列到现有表
        migrations = [
            ("health_records", "family_member_id", "INTEGER"),
            ("health_records", "value_extra", "TEXT"),
            ("health_records", "tags", "TEXT"),
            ("health_records", "assessment_result", "TEXT"),
            ("health_records", "advice", "TEXT"),
            ("family_members", "avatar_color", "TEXT"),
            ("family_members", "health_summary", "TEXT"),
            ("family_members", "last_checkin_at", "TEXT"),
            ("checkins", "family_member_id", "INTEGER"),
            ("checkins", "checkin_task_id", "INTEGER"),
            ("checkins", "streak_days", "INTEGER DEFAULT 0"),
            ("checkins", "mood", "TEXT"),
            ("checkins", "weather", "TEXT"),
            ("notifications", "family_member_id", "INTEGER"),
            ("notifications", "priority", "TEXT DEFAULT 'normal'"),
            ("notifications", "action_url", "TEXT"),
            ("notifications", "read_at", "TEXT"),
        ]
        for table, column, col_type in migrations:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except:
                pass
        conn.commit()

        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
            conn.commit()
        except Exception:
            conn.rollback()
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN scene TEXT")
            conn.commit()
        except Exception:
            conn.rollback()
        for sql in [
            "ALTER TABLE users ADD COLUMN phone TEXT",
            "ALTER TABLE users ADD COLUMN id_number TEXT",
            "ALTER TABLE health_profiles ADD COLUMN address TEXT",
        ]:
            try:
                conn.execute(sql)
                conn.commit()
            except Exception:
                conn.rollback()
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_id_number ON users(id_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_att_msg ON message_attachments(message_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_att_user ON message_attachments(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON medical_documents(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        conn.commit()

        # 新功能：健康数据记录表（增强版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                family_member_id INTEGER,
                record_type TEXT NOT NULL,
                value REAL NOT NULL,
                value_extra TEXT,
                unit TEXT,
                tags TEXT,
                assessment_result TEXT,
                advice TEXT,
                note TEXT,
                recorded_at TEXT,
                created_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_health_records_user ON health_records(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_health_records_member ON health_records(family_member_id)")

        # 新功能：家庭成员表（增强版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                gender TEXT,
                age INTEGER,
                relation TEXT,
                phone TEXT,
                chronic_diseases TEXT,
                allergy_history TEXT,
                avatar_color TEXT,
                health_summary TEXT,
                last_checkin_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_family_members_user ON family_members(user_id)")

        # 新功能：健康打卡表（增强版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                family_member_id INTEGER,
                checkin_type TEXT NOT NULL,
                checkin_task_id INTEGER,
                status TEXT DEFAULT 'done',
                streak_days INTEGER DEFAULT 0,
                note TEXT,
                mood TEXT,
                weather TEXT,
                checked_at TEXT,
                created_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkins_member ON checkins(family_member_id)")

        # 新功能：打卡任务/习惯表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkin_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                family_member_id INTEGER,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                target_days TEXT,
                reminder_time TEXT,
                reminder_enabled INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                total_completed INTEGER DEFAULT 0,
                last_completed_at TEXT,
                start_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkin_tasks_user ON checkin_tasks(user_id)")

        # 新功能：收藏表（增强版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fav_type TEXT NOT NULL,
                target_id TEXT,
                title TEXT,
                content TEXT,
                tags TEXT,
                related_record_id INTEGER,
                related_member_id INTEGER,
                color TEXT,
                created_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)")

        # 新功能：消息通知表（增强版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                family_member_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                notif_type TEXT,
                priority TEXT DEFAULT 'normal',
                action_url TEXT,
                is_read INTEGER DEFAULT 0,
                read_at TEXT,
                created_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")

        # 新功能：健康目标表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS health_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                family_member_id INTEGER,
                goal_type TEXT NOT NULL,
                goal_name TEXT NOT NULL,
                target_value REAL,
                current_value REAL,
                unit TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'active',
                progress INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_health_goals_user ON health_goals(user_id)")

        # 新功能：健康洞察表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS health_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                data_snapshot TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_health_insights_user ON health_insights(user_id)")

        conn.commit()


def create_user(
    username: str,
    password_hash: str,
    display_name: str = "",
    phone: str = "",
    id_number: str = "",
) -> Dict[str, Any]:
    user_id = uuid.uuid4().hex
    ts = now_text()
    with get_conn() as conn:
        _execute(
            conn,
            """
            INSERT INTO users(user_id, username, phone, id_number, password_hash, display_name, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, phone or username, id_number, password_hash, display_name or username, ts, ts),
        )
        conn.commit()
    return {
        "user_id": user_id,
        "username": username,
        "phone": phone or username,
        "id_number": id_number,
        "display_name": display_name or username,
    }


def get_user_by_username(username: str) -> Dict[str, Any] | None:
    with get_conn() as conn:
        row = _execute(
            conn,
            """
            SELECT u.*, h.age, h.gender, h.chronic_diseases, h.allergy_history,
                   h.medication_history, h.address
            FROM users u
            LEFT JOIN health_profiles h ON h.user_id = u.user_id
            WHERE u.username=? OR u.phone=?
            """,
            (username, username),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_id(user_id: str) -> Dict[str, Any] | None:
    with get_conn() as conn:
        row = _execute(
            conn,
            """
            SELECT u.*, h.age, h.gender, h.chronic_diseases, h.allergy_history,
                   h.medication_history, h.address
            FROM users u
            LEFT JOIN health_profiles h ON h.user_id = u.user_id
            WHERE u.user_id=?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def update_user_profile(
    user_id: str,
    *,
    phone: str | None = None,
    display_name: str | None = None,
    password_hash: str | None = None,
    age: int | None = None,
    gender: str | None = None,
    address: str | None = None,
    chronic_diseases: str | None = None,
    allergy_history: str | None = None,
    medication_history: str | None = None,
) -> Dict[str, Any]:
    with get_conn() as conn:
        fields: List[str] = []
        params: List[Any] = []
        if phone is not None:
            fields.extend(["username=?", "phone=?"])
            params.extend([phone, phone])
        if display_name is not None:
            fields.append("display_name=?")
            params.append(display_name)
        if password_hash is not None:
            fields.append("password_hash=?")
            params.append(password_hash)
        if fields:
            params.append(user_id)
            _execute(conn, f"UPDATE users SET {', '.join(fields)} WHERE user_id=?", params)
        _execute(
            conn,
            """
            INSERT INTO health_profiles(
                user_id, age, gender, chronic_diseases, allergy_history,
                medication_history, address, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                age=COALESCE(excluded.age, health_profiles.age),
                gender=COALESCE(excluded.gender, health_profiles.gender),
                chronic_diseases=COALESCE(excluded.chronic_diseases, health_profiles.chronic_diseases),
                allergy_history=COALESCE(excluded.allergy_history, health_profiles.allergy_history),
                medication_history=COALESCE(excluded.medication_history, health_profiles.medication_history),
                address=COALESCE(excluded.address, health_profiles.address),
                updated_at=excluded.updated_at
            """,
            (
                user_id,
                age,
                gender,
                chronic_diseases,
                allergy_history,
                medication_history,
                address,
                now_text(),
            ),
        )
        conn.commit()
    return get_user_by_id(user_id) or {}


def touch_user_login(user_id: str) -> None:
    with get_conn() as conn:
        _execute(conn, "UPDATE users SET last_login_at=? WHERE user_id=?", (now_text(), user_id))
        conn.commit()


def upsert_session(session_id: str, title: str = "医疗问诊会话", user_id: str | None = None, scene: str | None = None) -> None:
    ts = now_text()
    with get_conn() as conn:
        _execute(
            conn,
            """
            INSERT INTO sessions(id, user_id, scene, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id=COALESCE(excluded.user_id, sessions.user_id),
                scene=COALESCE(excluded.scene, sessions.scene),
                title=COALESCE(NULLIF(excluded.title, ''), sessions.title),
                updated_at=excluded.updated_at
            """,
            (session_id, user_id, scene, title, ts, ts),
        )
        conn.commit()


def add_message(session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None) -> int:
    with get_conn() as conn:
        params = (session_id, role, content, json.dumps(metadata or {}, ensure_ascii=False), now_text())
        if USE_POSTGRES:
            cur = conn.execute(
                """
                INSERT INTO messages(session_id, role, content, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                params,
            )
            message_id = int(cur.fetchone()["id"])
        else:
            cur = _execute(
                conn,
                "INSERT INTO messages(session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                params,
            )
            message_id = int(cur.lastrowid)
        conn.commit()
        return message_id


def attach_documents_to_message(
    message_id: int,
    session_id: str | None,
    user_id: str,
    doc_ids: List[str],
) -> None:
    if not doc_ids:
        return
    ts = now_text()
    with get_conn() as conn:
        for position, doc_id in enumerate(doc_ids):
            row = _execute(conn, "SELECT user_id FROM medical_documents WHERE doc_id=?", (doc_id,)).fetchone()
            if not row or row["user_id"] != user_id:
                continue
            _execute(
                conn,
                """
                INSERT INTO message_attachments
                    (message_id, doc_id, user_id, session_id, position, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, doc_id, user_id, session_id, position, ts),
            )
        conn.commit()


def list_attachments_for_messages(message_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
    if not message_ids:
        return {}
    placeholders = _ph(len(message_ids))
    sql = f"""
        SELECT a.message_id, a.doc_id, a.position, a.created_at,
               d.file_name, d.doc_type, d.title, d.summary,
               d.confidence, d.page_count
        FROM message_attachments a
        LEFT JOIN medical_documents d ON a.doc_id = d.doc_id
        WHERE a.message_id IN ({placeholders})
        ORDER BY a.message_id ASC, a.position ASC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, message_ids).fetchall() if USE_POSTGRES else conn.execute(sql, message_ids).fetchall()
    out: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(int(row["message_id"]), []).append(
            {
                "doc_id": row["doc_id"],
                "position": row["position"],
                "file_name": row["file_name"],
                "doc_type": row["doc_type"],
                "title": row["title"],
                "summary": row["summary"],
                "confidence": row["confidence"],
                "page_count": row["page_count"],
                "raw_url": f"/api/upload/medical-document/{row['doc_id']}/raw",
            }
        )
    return out


def get_documents_by_ids(doc_ids: List[str], user_id: str) -> List[Dict[str, Any]]:
    if not doc_ids:
        return []
    placeholders = _ph(len(doc_ids))
    sql = f"SELECT * FROM medical_documents WHERE doc_id IN ({placeholders}) AND user_id={('%s' if USE_POSTGRES else '?')}"
    params = list(doc_ids) + [user_id]
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    by_id = {row["doc_id"]: row for row in rows}
    result: List[Dict[str, Any]] = []
    for doc_id in doc_ids:
        row = by_id.get(doc_id)
        if not row:
            continue
        item = _row_to_dict(row)
        item["parsed_json"] = json.loads(item.get("parsed_json") or "{}")
        result.append(item)
    return result


def list_session_medical_documents(
    session_id: str,
    user_id: str,
    limit: int = 8,
    exclude_doc_ids: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """按本会话附件关系取回用户报告，最近上传/引用的排前面。"""
    exclude_doc_ids = exclude_doc_ids or []
    params: List[Any] = [session_id, user_id]
    exclude_sql = ""
    if exclude_doc_ids:
        exclude_sql = f" AND d.doc_id NOT IN ({_ph(len(exclude_doc_ids))})"
        params.extend(exclude_doc_ids)
    params.append(limit)
    sql = f"""
        SELECT d.*, MAX(a.created_at) AS attached_at
        FROM message_attachments a
        JOIN medical_documents d ON d.doc_id = a.doc_id
        WHERE a.session_id=? AND a.user_id=? {exclude_sql}
        GROUP BY d.doc_id
        ORDER BY COALESCE(MAX(a.created_at), d.created_at) DESC
        LIMIT ?
    """
    with get_conn() as conn:
        rows = _execute(conn, sql, params).fetchall()
    result: List[Dict[str, Any]] = []
    for row in rows:
        item = _row_to_dict(row)
        item["parsed_json"] = json.loads(item.get("parsed_json") or "{}")
        result.append(item)
    return result


def list_messages(session_id: str, limit: int = 20, with_attachments: bool = False) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = _execute(
            conn,
            "SELECT id, role, content, metadata, created_at FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    messages = [
        {
            "id": int(row["id"]),
            "role": row["role"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"] or "{}"),
            "created_at": row["created_at"],
        }
        for row in reversed(rows)
    ]
    if with_attachments and messages:
        att_map = list_attachments_for_messages([m["id"] for m in messages])
        for msg in messages:
            msg["attachments"] = att_map.get(msg["id"], [])
    return messages


def list_sessions(limit: int = 50, user_id: str | None = None, scene: str | None = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        if user_id and scene:
            rows = _execute(
                conn,
                "SELECT id, user_id, scene, title, created_at, updated_at FROM sessions WHERE user_id=? AND scene=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, scene, limit),
            ).fetchall()
        elif user_id:
            rows = _execute(
                conn,
                "SELECT id, user_id, scene, title, created_at, updated_at FROM sessions WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT id, user_id, scene, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def session_belongs_to_user(session_id: str, user_id: str) -> bool:
    with get_conn() as conn:
        row = _execute(conn, "SELECT user_id FROM sessions WHERE id=?", (session_id,)).fetchone()
    return bool(row and row["user_id"] == user_id)


def add_encounter(
    session_id: str,
    user_id: str,
    scene: str,
    chief_complaint: str,
    risk_level: str,
    department: str,
    summary: str,
    metadata: Dict[str, Any] | None = None,
) -> None:
    with get_conn() as conn:
        _execute(
            conn,
            """
            INSERT INTO encounters(session_id, user_id, scene, chief_complaint, risk_level, department, summary, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                scene,
                chief_complaint,
                risk_level,
                department,
                summary,
                json.dumps(metadata or {}, ensure_ascii=False),
                now_text(),
            ),
        )
        conn.commit()


def list_encounters(user_id: str = "demo_user", days: int = 7) -> List[Dict[str, Any]]:
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = _execute(
            conn,
            """
            SELECT * FROM encounters
            WHERE user_id=? AND created_at>=?
            ORDER BY created_at DESC
            """,
            (user_id, since),
        ).fetchall()
    result = []
    for row in rows:
        item = _row_to_dict(row)
        item["metadata"] = json.loads(item.get("metadata") or "{}")
        result.append(item)
    return result


def add_appointment(payload: Dict[str, Any]) -> int:
    with get_conn() as conn:
        existing = _execute(
            conn,
            """
            SELECT id FROM appointments
            WHERE user_id=? AND department=? AND doctor=? AND visit_date=? AND period=? AND time_slot=? AND status='已预约'
            LIMIT 1
            """,
            (
                payload.get("user_id", "demo_user"),
                payload["department"],
                payload["doctor"],
                payload["visit_date"],
                payload["period"],
                payload["time_slot"],
            ),
        ).fetchone()
        if existing:
            return int(existing["id"])
        if USE_POSTGRES:
            cur = conn.execute(
                """
                INSERT INTO appointments(user_id, department, doctor, doctor_title, visit_date, period, time_slot, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    payload.get("user_id", "demo_user"),
                    payload["department"],
                    payload["doctor"],
                    payload.get("doctor_title", ""),
                    payload["visit_date"],
                    payload["period"],
                    payload["time_slot"],
                    "已预约",
                    now_text(),
                ),
            )
            appointment_id = int(cur.fetchone()["id"])
        else:
            cur = conn.execute(
                """
                INSERT INTO appointments(user_id, department, doctor, doctor_title, visit_date, period, time_slot, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get("user_id", "demo_user"),
                    payload["department"],
                    payload["doctor"],
                    payload.get("doctor_title", ""),
                    payload["visit_date"],
                    payload["period"],
                    payload["time_slot"],
                    "已预约",
                    now_text(),
                ),
            )
            appointment_id = int(cur.lastrowid)
        conn.commit()
        return appointment_id


def list_appointments(user_id: str = "demo_user") -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = _execute(
            conn,
            """
            SELECT * FROM appointments
            WHERE user_id=?
            ORDER BY visit_date ASC, period ASC, time_slot ASC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def cancel_appointment(appointment_id: int, user_id: str = "demo_user") -> bool:
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            UPDATE appointments
            SET status='已取消'
            WHERE id=? AND user_id=? AND status='已预约'
            """,
            (appointment_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def appointment_counts(user_id: str = "demo_user") -> Dict[str, int]:
    with get_conn() as conn:
        rows = _execute(
            conn,
            """
            SELECT department, doctor, visit_date, period, time_slot, COUNT(*) AS total
            FROM appointments
            WHERE user_id=? AND status='已预约'
            GROUP BY department, doctor, visit_date, period, time_slot
            """,
            (user_id,),
        ).fetchall()
    counts: Dict[str, int] = {}
    for row in rows:
        key = appointment_key(row["department"], row["doctor"], row["visit_date"], row["period"], row["time_slot"])
        counts[key] = int(row["total"])
    return counts


def appointment_key(department: str, doctor: str, visit_date: str, period: str, time_slot: str) -> str:
    return f"{department}|{doctor}|{visit_date}|{period}|{time_slot}"


def add_medical_document(
    doc_id: str,
    user_id: str,
    session_id: str | None,
    file_name: str,
    file_path: str,
    doc_type: str,
    title: str,
    summary: str,
    parsed: Dict[str, Any],
    confidence: float,
    page_count: int,
) -> None:
    with get_conn() as conn:
        _execute(
            conn,
            """
            INSERT INTO medical_documents
                (doc_id, user_id, session_id, file_name, file_path, doc_type,
                 title, summary, parsed_json, confidence, page_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                user_id=excluded.user_id,
                session_id=excluded.session_id,
                file_name=excluded.file_name,
                file_path=excluded.file_path,
                doc_type=excluded.doc_type,
                title=excluded.title,
                summary=excluded.summary,
                parsed_json=excluded.parsed_json,
                confidence=excluded.confidence,
                page_count=excluded.page_count,
                created_at=excluded.created_at
            """,
            (
                doc_id,
                user_id,
                session_id,
                file_name,
                file_path,
                doc_type,
                title,
                summary,
                json.dumps(parsed, ensure_ascii=False),
                float(confidence or 0.0),
                int(page_count or 0),
                now_text(),
            ),
        )
        conn.commit()


def list_medical_documents(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = _execute(
            conn,
            """
            SELECT doc_id, user_id, session_id, file_name, doc_type, title, summary,
                   parsed_json, confidence, page_count, created_at
            FROM medical_documents
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        item = _row_to_dict(row)
        parsed = json.loads(item.pop("parsed_json") or "{}")
        item["parse_status"] = parsed.get("parse_status") or "ok"
        item["items"] = parsed.get("items") or []
        item["key_abnormalities"] = parsed.get("key_abnormalities") or []
        item["findings"] = parsed.get("findings") or ""
        item["impression"] = parsed.get("impression") or ""
        item["duration_ms"] = (parsed.get("processing") or {}).get("duration_ms")
        result.append(item)
    return result


def get_medical_document(doc_id: str) -> Dict[str, Any] | None:
    with get_conn() as conn:
        row = _execute(conn, "SELECT * FROM medical_documents WHERE doc_id=?", (doc_id,)).fetchone()
    if not row:
        return None
    item = _row_to_dict(row)
    item["parsed_json"] = json.loads(item.get("parsed_json") or "{}")
    return item


def list_all_medical_documents() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = _execute(conn, "SELECT * FROM medical_documents ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_medical_document(doc_id: str, user_id: str) -> bool:
    with get_conn() as conn:
        cur = _execute(
            conn,
            "DELETE FROM medical_documents WHERE doc_id=? AND user_id=?",
            (doc_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_report_sessions_for_user(user_id: str) -> int:
    """删除当前用户上传报告参与过的会话，避免旧回答继续污染医疗记忆。"""
    with get_conn() as conn:
        rows = _execute(
            conn,
            "SELECT DISTINCT session_id FROM message_attachments WHERE user_id=? AND session_id IS NOT NULL",
            (user_id,),
        ).fetchall()
        session_ids = [row["session_id"] for row in rows if row["session_id"]]
        if session_ids:
            placeholders = _ph(len(session_ids))
            params = list(session_ids)
            conn.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", params)
            conn.execute(f"DELETE FROM encounters WHERE session_id IN ({placeholders})", params)
            conn.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", params)
        conn.commit()
        return len(session_ids)


def delete_all_report_sessions() -> int:
    """删除所有带报告附件的会话；用于后台全量清理报告记忆。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT session_id FROM message_attachments WHERE session_id IS NOT NULL"
        ).fetchall()
        session_ids = [row["session_id"] for row in rows if row["session_id"]]
        if session_ids:
            placeholders = _ph(len(session_ids))
            params = list(session_ids)
            conn.execute(f"DELETE FROM messages WHERE session_id IN ({placeholders})", params)
            conn.execute(f"DELETE FROM encounters WHERE session_id IN ({placeholders})", params)
            conn.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", params)
        conn.commit()
        return len(session_ids)


def delete_medical_documents_for_user(user_id: str) -> int:
    with get_conn() as conn:
        _execute(conn, "DELETE FROM message_attachments WHERE user_id=?", (user_id,))
        cur = _execute(conn, "DELETE FROM medical_documents WHERE user_id=?", (user_id,))
        conn.commit()
        return cur.rowcount


def delete_all_medical_documents() -> int:
    with get_conn() as conn:
        conn.execute("DELETE FROM message_attachments")
        cur = conn.execute("DELETE FROM medical_documents")
        conn.commit()
        return cur.rowcount


def clear_session(session_id: str, user_id: str | None = None) -> None:
    with get_conn() as conn:
        if user_id:
            row = _execute(conn, "SELECT user_id FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row or row["user_id"] != user_id:
                return
        _execute(conn, "DELETE FROM messages WHERE session_id=?", (session_id,))
        _execute(conn, "DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()


def clear_all(user_id: str | None = None) -> None:
    with get_conn() as conn:
        if user_id:
            _execute(conn, "DELETE FROM messages WHERE session_id IN (SELECT id FROM sessions WHERE user_id=?)", (user_id,))
            _execute(conn, "DELETE FROM sessions WHERE user_id=?", (user_id,))
            _execute(conn, "DELETE FROM encounters WHERE user_id=?", (user_id,))
            _execute(conn, "DELETE FROM appointments WHERE user_id=?", (user_id,))
        else:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM encounters")
            conn.execute("DELETE FROM appointments")
        conn.commit()


# ==================== 新功能：健康数据记录（增强版）====================
def add_health_record(
    user_id: str,
    record_type: str,
    value: float,
    unit: str = "",
    note: str = "",
    recorded_at: str = "",
    family_member_id: int = None,
    value_extra: float = None,
    tags: str = "",
    assessment_result: str = "",
    advice: str = ""
) -> int:
    """添加健康数据记录（增强版，支持评估和建议）"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO health_records(user_id, family_member_id, record_type, value, value_extra, unit, tags, assessment_result, advice, note, recorded_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, family_member_id, record_type, value, value_extra, unit, tags, assessment_result, advice, note, recorded_at or ts, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_health_records(user_id: str, record_type: str | None = None, days: int = 30, family_member_id: int = None) -> list:
    """获取健康数据记录列表（支持筛选）"""
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        if record_type and family_member_id:
            rows = _execute(
                conn,
                "SELECT * FROM health_records WHERE user_id=? AND record_type=? AND family_member_id=? AND created_at>=? ORDER BY recorded_at DESC",
                (user_id, record_type, family_member_id, since),
            ).fetchall()
        elif record_type:
            rows = _execute(
                conn,
                "SELECT * FROM health_records WHERE user_id=? AND record_type=? AND created_at>=? ORDER BY recorded_at DESC",
                (user_id, record_type, since),
            ).fetchall()
        elif family_member_id:
            rows = _execute(
                conn,
                "SELECT * FROM health_records WHERE user_id=? AND family_member_id=? AND created_at>=? ORDER BY recorded_at DESC",
                (user_id, family_member_id, since),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM health_records WHERE user_id=? AND created_at>=? ORDER BY recorded_at DESC",
                (user_id, since),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_health_trends(user_id: str, record_type: str, days: int = 30) -> dict:
    """获取健康数据趋势分析"""
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        rows = _execute(
            conn,
            "SELECT * FROM health_records WHERE user_id=? AND record_type=? AND created_at>=? ORDER BY recorded_at ASC",
            (user_id, record_type, since),
        ).fetchall()
    records = [_row_to_dict(row) for row in rows]
    if not records:
        return {"records": [], "avg": None, "min": None, "max": None, "trend": "stable"}
    values = [r["value"] for r in records]
    avg = sum(values) / len(values)
    minimum = min(values)
    maximum = max(values)
    # 计算趋势
    if len(values) >= 3:
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        if second_half_avg > first_half_avg * 1.05:
            trend = "rising"
        elif second_half_avg < first_half_avg * 0.95:
            trend = "falling"
        else:
            trend = "stable"
    else:
        trend = "stable"
    return {"records": records, "avg": round(avg, 2), "min": minimum, "max": maximum, "trend": trend, "count": len(values)}


def delete_health_record(record_id: int, user_id: str) -> bool:
    """删除健康记录"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM health_records WHERE id=? AND user_id=?", (record_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：家庭成员管理（增强版）====================
def add_family_member(
    user_id: str,
    name: str,
    gender: str = "",
    age: int = 0,
    relation: str = "",
    phone: str = "",
    chronic_diseases: str = "",
    allergy_history: str = "",
    avatar_color: str = ""
) -> int:
    """添加家庭成员（增强版）"""
    ts = now_text()
    if not avatar_color:
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]
        # 使用哈希值而不是时间戳最后4位来生成颜色，避免格式问题
        import hashlib
        name_hash = int(hashlib.md5(name.encode()).hexdigest()[:4], 16)
        avatar_color = colors[name_hash % len(colors)]
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO family_members(user_id, name, gender, age, relation, phone, chronic_diseases, allergy_history, avatar_color, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, gender, age, relation, phone, chronic_diseases, allergy_history, avatar_color, ts, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_family_members(user_id: str) -> list:
    """获取家庭成员列表（包含健康汇总）"""
    members = []
    with get_conn() as conn:
        rows = _execute(
            conn,
            "SELECT * FROM family_members WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    for row in rows:
        member = _row_to_dict(row)
        # 获取成员最近健康数据
        recent_records = list_health_records(user_id, days=7, family_member_id=member["id"])
        recent_checkins = list_checkins(user_id, days=7, family_member_id=member["id"])
        member["recent_records"] = recent_records[:3] if recent_records else []
        member["recent_checkins"] = recent_checkins[:3] if recent_checkins else []
        member["checkin_count_7d"] = len(recent_checkins)
        members.append(member)
    return members


def update_family_member(
    member_id: int,
    user_id: str,
    name: str = None,
    gender: str = None,
    age: int = None,
    relation: str = None,
    phone: str = None,
    chronic_diseases: str = None,
    allergy_history: str = None,
    avatar_color: str = None,
    health_summary: str = None,
    last_checkin_at: str = None
) -> bool:
    """更新家庭成员信息（增强版）"""
    fields = []
    params = []
    if name is not None:
        fields.append("name=?")
        params.append(name)
    if gender is not None:
        fields.append("gender=?")
        params.append(gender)
    if age is not None:
        fields.append("age=?")
        params.append(age)
    if relation is not None:
        fields.append("relation=?")
        params.append(relation)
    if phone is not None:
        fields.append("phone=?")
        params.append(phone)
    if chronic_diseases is not None:
        fields.append("chronic_diseases=?")
        params.append(chronic_diseases)
    if allergy_history is not None:
        fields.append("allergy_history=?")
        params.append(allergy_history)
    if avatar_color is not None:
        fields.append("avatar_color=?")
        params.append(avatar_color)
    if health_summary is not None:
        fields.append("health_summary=?")
        params.append(health_summary)
    if last_checkin_at is not None:
        fields.append("last_checkin_at=?")
        params.append(last_checkin_at)
    if not fields:
        return False
    fields.append("updated_at=?")
    params.append(now_text())
    params.extend([member_id, user_id])
    with get_conn() as conn:
        cur = _execute(conn, f"UPDATE family_members SET {', '.join(fields)} WHERE id=? AND user_id=?", params)
        conn.commit()
        return cur.rowcount > 0


def delete_family_member(member_id: int, user_id: str) -> bool:
    """删除家庭成员"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM family_members WHERE id=? AND user_id=?", (member_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：健康打卡（增强版）====================
def add_checkin(
    user_id: str,
    checkin_type: str,
    status: str = "done",
    note: str = "",
    checked_at: str = "",
    family_member_id: int = None,
    checkin_task_id: int = None,
    streak_days: int = 0,
    mood: str = "",
    weather: str = ""
) -> int:
    """添加健康打卡（增强版）"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO checkins(user_id, family_member_id, checkin_type, checkin_task_id, status, streak_days, note, mood, weather, checked_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, family_member_id, checkin_type, checkin_task_id, status, streak_days, note, mood, weather, checked_at or ts, ts),
        )
        conn.commit()
        new_id = int(cur.lastrowid)
        # 更新打卡任务的连续天数
        if checkin_task_id:
            _update_checkin_task_streak(conn, checkin_task_id)
        # 更新家庭成员最后打卡时间
        if family_member_id:
            _execute(conn, "UPDATE family_members SET last_checkin_at=? WHERE id=?", (ts, family_member_id))
            conn.commit()
        return new_id


def _update_checkin_task_streak(conn, task_id: int) -> None:
    """更新打卡任务的连续天数"""
    ts = now_text()
    task = conn.execute("SELECT * FROM checkin_tasks WHERE id=?", (task_id,)).fetchone()
    if task:
        last_completed = task["last_completed_at"]
        current_streak = task["current_streak"]
        if last_completed:
            last_date = datetime.fromisoformat(last_completed)
            today = datetime.now()
            if last_date.date() == (today - timedelta(days=1)).date():
                current_streak += 1
            elif last_date.date() == today.date():
                pass  # 今天已完成
            else:
                current_streak = 1  # 断开，重新开始
        else:
            current_streak = 1
        best_streak = max(current_streak, task["best_streak"])
        total = task["total_completed"] + 1
        _execute(conn,
            "UPDATE checkin_tasks SET current_streak=?, best_streak=?, total_completed=?, last_completed_at=? WHERE id=?",
            (current_streak, best_streak, total, ts, task_id)
        )


def list_checkins(user_id: str, days: int = 30, family_member_id: int = None, checkin_type: str = None) -> list:
    """获取健康打卡列表（支持筛选）"""
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with get_conn() as conn:
        if family_member_id and checkin_type:
            rows = _execute(
                conn,
                "SELECT * FROM checkins WHERE user_id=? AND family_member_id=? AND checkin_type=? AND created_at>=? ORDER BY checked_at DESC",
                (user_id, family_member_id, checkin_type, since),
            ).fetchall()
        elif family_member_id:
            rows = _execute(
                conn,
                "SELECT * FROM checkins WHERE user_id=? AND family_member_id=? AND created_at>=? ORDER BY checked_at DESC",
                (user_id, family_member_id, since),
            ).fetchall()
        elif checkin_type:
            rows = _execute(
                conn,
                "SELECT * FROM checkins WHERE user_id=? AND checkin_type=? AND created_at>=? ORDER BY checked_at DESC",
                (user_id, checkin_type, since),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM checkins WHERE user_id=? AND created_at>=? ORDER BY checked_at DESC",
                (user_id, since),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_checkin(checkin_id: int, user_id: str) -> bool:
    """删除健康打卡"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM checkins WHERE id=? AND user_id=?", (checkin_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：打卡任务/习惯 ====================
def add_checkin_task(
    user_id: str,
    task_name: str,
    task_type: str,
    family_member_id: int = None,
    target_days: str = "",
    reminder_time: str = "",
    reminder_enabled: bool = False,
    start_date: str = ""
) -> int:
    """添加打卡任务"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO checkin_tasks(user_id, family_member_id, task_name, task_type, target_days, reminder_time, reminder_enabled, start_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, family_member_id, task_name, task_type, target_days, reminder_time, 1 if reminder_enabled else 0, start_date or ts, ts, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_checkin_tasks(user_id: str, active_only: bool = True) -> list:
    """获取打卡任务列表"""
    with get_conn() as conn:
        if active_only:
            rows = _execute(
                conn,
                "SELECT * FROM checkin_tasks WHERE user_id=? AND is_active=1 ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM checkin_tasks WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_checkin_task(task_id: int, user_id: str) -> bool:
    """删除打卡任务"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM checkin_tasks WHERE id=? AND user_id=?", (task_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：收藏（增强版）====================
def add_favorite(
    user_id: str,
    fav_type: str,
    target_id: str = "",
    title: str = "",
    content: str = "",
    tags: str = "",
    related_record_id: int = None,
    related_member_id: int = None,
    color: str = ""
) -> int:
    """添加收藏（增强版）"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO favorites(user_id, fav_type, target_id, title, content, tags, related_record_id, related_member_id, color, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, fav_type, target_id, title, content, tags, related_record_id, related_member_id, color, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_favorites(user_id: str, fav_type: str | None = None, tags: str | None = None) -> list:
    """获取收藏列表（支持标签筛选）"""
    with get_conn() as conn:
        if fav_type and tags:
            rows = _execute(
                conn,
                "SELECT * FROM favorites WHERE user_id=? AND fav_type=? AND tags LIKE ? ORDER BY created_at DESC",
                (user_id, fav_type, f"%{tags}%"),
            ).fetchall()
        elif fav_type:
            rows = _execute(
                conn,
                "SELECT * FROM favorites WHERE user_id=? AND fav_type=? ORDER BY created_at DESC",
                (user_id, fav_type),
            ).fetchall()
        elif tags:
            rows = _execute(
                conn,
                "SELECT * FROM favorites WHERE user_id=? AND tags LIKE ? ORDER BY created_at DESC",
                (user_id, f"%{tags}%"),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM favorites WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def delete_favorite(favorite_id: int, user_id: str) -> bool:
    """删除收藏"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM favorites WHERE id=? AND user_id=?", (favorite_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：消息通知（增强版）====================
def add_notification(
    user_id: str,
    title: str,
    content: str = "",
    notif_type: str = "info",
    priority: str = "normal",
    family_member_id: int = None,
    action_url: str = ""
) -> int:
    """添加消息通知（增强版）"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO notifications(user_id, family_member_id, title, content, notif_type, priority, action_url, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (user_id, family_member_id, title, content, notif_type, priority, action_url, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_notifications(user_id: str, include_read: bool = True, notif_type: str = None) -> list:
    """获取消息通知列表（支持类型筛选）"""
    with get_conn() as conn:
        if not include_read:
            if notif_type:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND is_read=0 AND notif_type=? ORDER BY created_at DESC LIMIT 50",
                    (user_id, notif_type),
                ).fetchall()
            else:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC LIMIT 50",
                    (user_id,),
                ).fetchall()
        else:
            if notif_type:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND notif_type=? ORDER BY created_at DESC LIMIT 50",
                    (user_id, notif_type),
                ).fetchall()
            else:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
                    (user_id,),
                ).fetchall()
    return [_row_to_dict(row) for row in rows]


def mark_notification_read(notif_id: int, user_id: str) -> bool:
    """标记通知为已读"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(conn, "UPDATE notifications SET is_read=1, read_at=? WHERE id=? AND user_id=?", (ts, notif_id, user_id))
        conn.commit()
        return cur.rowcount > 0


def mark_all_notifications_read(user_id: str) -> int:
    """标记所有通知为已读"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(conn, "UPDATE notifications SET is_read=1, read_at=? WHERE user_id=? AND is_read=0", (ts, user_id))
        conn.commit()
        return cur.rowcount


def get_unread_notification_count(user_id: str, notif_type: str = None) -> int:
    """获取未读通知数量"""
    with get_conn() as conn:
        if notif_type:
            row = _execute(conn, "SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0 AND notif_type=?", (user_id, notif_type)).fetchone()
        else:
            row = _execute(conn, "SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0", (user_id,)).fetchone()
    return int(row["cnt"]) if row else 0


def delete_notification(notif_id: int, user_id: str) -> bool:
    """删除通知"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM notifications WHERE id=? AND user_id=?", (notif_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：健康目标 ====================
def add_health_goal(
    user_id: str,
    goal_name: str,
    goal_type: str,
    target_value: float = None,
    unit: str = "",
    deadline: str = "",
    family_member_id: int = None
) -> int:
    """添加健康目标"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO health_goals(user_id, family_member_id, goal_type, goal_name, target_value, unit, deadline, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, family_member_id, goal_type, goal_name, target_value, unit, deadline, ts, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_health_goals(user_id: str, active_only: bool = True) -> list:
    """获取健康目标列表"""
    with get_conn() as conn:
        if active_only:
            rows = _execute(
                conn,
                "SELECT * FROM health_goals WHERE user_id=? AND status='active' ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM health_goals WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def update_health_goal_progress(goal_id: int, current_value: float, user_id: str) -> bool:
    """更新健康目标进度"""
    with get_conn() as conn:
        goal = conn.execute("SELECT * FROM health_goals WHERE id=? AND user_id=?", (goal_id, user_id)).fetchone()
        if not goal:
            return False
        progress = int((current_value / goal["target_value"]) * 100) if goal["target_value"] else 0
        status = "completed" if progress >= 100 else "active"
        cur = _execute(
            conn,
            "UPDATE health_goals SET current_value=?, progress=?, status=?, updated_at=? WHERE id=? AND user_id=?",
            (current_value, min(progress, 100), status, now_text(), goal_id, user_id)
        )
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：健康洞察 ====================
def add_health_insight(
    user_id: str,
    insight_type: str,
    title: str,
    content: str = "",
    data_snapshot: str = ""
) -> int:
    """添加健康洞察"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO health_insights(user_id, insight_type, title, content, data_snapshot, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, insight_type, title, content, data_snapshot, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_health_insights(user_id: str, unread_only: bool = False) -> list:
    """获取健康洞察列表"""
    with get_conn() as conn:
        if unread_only:
            rows = _execute(
                conn,
                "SELECT * FROM health_insights WHERE user_id=? AND is_read=0 ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = _execute(
                conn,
                "SELECT * FROM health_insights WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows]


def mark_insight_read(insight_id: int, user_id: str) -> bool:
    """标记洞察为已读"""
    with get_conn() as conn:
        cur = _execute(conn, "UPDATE health_insights SET is_read=1 WHERE id=? AND user_id=?", (insight_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：智能健康评估 ====================
def assess_health_data(record_type: str, value: float, value_extra: float = None) -> tuple:
    """智能评估健康数据，返回(评估结果, 建议)"""
    if record_type == "血压":
        systolic = value
        diastolic = value_extra if value_extra else 0
        if systolic < 120 and diastolic < 80:
            return "正常", "血压保持在健康范围内，请继续保持良好的生活习惯。"
        elif systolic < 130 and diastolic < 80:
            return "偏高", "血压略高于正常值，建议减少盐分摄入，适量运动，保持充足睡眠。"
        elif systolic < 140 or diastolic < 90:
            return "高血压前期", "血压处于高血压前期，建议积极改善生活方式，减少高脂肪食物摄入，避免情绪激动。如有不适请及时就医。"
        else:
            return "高血压", "血压明显升高，建议尽快就医，根据医生建议进行管理和治疗。避免高盐高脂饮食，戒烟限酒。"
    elif record_type == "血糖":
        if value < 3.9:
            return "偏低", "血糖偏低，建议及时补充糖分，适当增加碳水化合物摄入。如有频繁发生请咨询医生。"
        elif value < 6.1:
            return "正常", "空腹血糖在正常范围内，请继续保持均衡饮食和适量运动。"
        elif value < 7.0:
            return "偏高", "空腹血糖偏高，处于糖尿病前期阶段。建议控制饮食，减少糖分摄入，增加运动量，并定期监测血糖。"
        else:
            return "高血糖", "空腹血糖明显升高，糖尿病风险较高。建议尽早就医检查，按医嘱进行饮食控制和必要治疗。"
    elif record_type == "体重":
        return "已记录", "体重数据已记录，请结合身高和BMI综合评估健康状况。保持健康体重对预防慢性疾病很重要。"
    return "已记录", "数据已记录，请关注长期趋势变化。"


# ==================== 新功能：健康数据统计 ====================
def get_health_stats(user_id: str) -> dict:
    """获取用户健康数据统计"""
    stats = {
        "total_records": 0,
        "records_by_type": {},
        "total_checkins": 0,
        "checkins_by_type": {},
        "active_goals": 0,
        "active_tasks": 0,
        "family_members_count": 0,
        "unread_insights": 0,
        "unread_notifications": 0
    }
    with get_conn() as conn:
        # 健康记录统计
        rows = _execute(conn, "SELECT record_type, COUNT(*) as cnt FROM health_records WHERE user_id=? GROUP BY record_type", (user_id,)).fetchall()
        for row in rows:
            stats["records_by_type"][row["record_type"]] = row["cnt"]
            stats["total_records"] += row["cnt"]
        # 打卡统计
        rows = _execute(conn, "SELECT checkin_type, COUNT(*) as cnt FROM checkins WHERE user_id=? GROUP BY checkin_type", (user_id,)).fetchall()
        for row in rows:
            stats["checkins_by_type"][row["checkin_type"]] = row["cnt"]
            stats["total_checkins"] += row["cnt"]
        # 其他统计
        stats["active_goals"] = conn.execute("SELECT COUNT(*) FROM health_goals WHERE user_id=? AND status='active'", (user_id,)).fetchone()[0]
        stats["active_tasks"] = conn.execute("SELECT COUNT(*) FROM checkin_tasks WHERE user_id=? AND is_active=1", (user_id,)).fetchone()[0]
        stats["family_members_count"] = conn.execute("SELECT COUNT(*) FROM family_members WHERE user_id=?", (user_id,)).fetchone()[0]
        stats["unread_insights"] = conn.execute("SELECT COUNT(*) FROM health_insights WHERE user_id=? AND is_read=0", (user_id,)).fetchone()[0]
        stats["unread_notifications"] = conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,)).fetchone()[0]
    return stats


def delete_favorite(favorite_id: int, user_id: str) -> bool:
    """删除收藏"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM favorites WHERE id=? AND user_id=?", (favorite_id, user_id))
        conn.commit()
        return cur.rowcount > 0


# ==================== 新功能：消息通知 ====================
def add_notification(
    user_id: str,
    title: str,
    content: str = "",
    notif_type: str = "info"
) -> int:
    """添加消息通知"""
    ts = now_text()
    with get_conn() as conn:
        cur = _execute(
            conn,
            """
            INSERT INTO notifications(user_id, title, content, notif_type, is_read, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (user_id, title, content, notif_type, ts),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_notifications(user_id: str, include_read: bool = True, notif_type: str = None) -> list:
    """获取消息通知列表"""
    with get_conn() as conn:
        if notif_type:
            if include_read:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND type=? ORDER BY created_at DESC LIMIT 50",
                    (user_id, notif_type),
                ).fetchall()
            else:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND type=? AND is_read=0 ORDER BY created_at DESC LIMIT 50",
                    (user_id, notif_type),
                ).fetchall()
        else:
            if include_read:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
                    (user_id,),
                ).fetchall()
            else:
                rows = _execute(
                    conn,
                    "SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC LIMIT 50",
                    (user_id,),
                ).fetchall()
    return [_row_to_dict(row) for row in rows]


def mark_notification_read(notif_id: int, user_id: str) -> bool:
    """标记通知为已读"""
    with get_conn() as conn:
        cur = _execute(conn, "UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notif_id, user_id))
        conn.commit()
        return cur.rowcount > 0


def mark_all_notifications_read(user_id: str) -> int:
    """标记所有通知为已读"""
    with get_conn() as conn:
        cur = _execute(conn, "UPDATE notifications SET is_read=1 WHERE user_id=? AND is_read=0", (user_id,))
        conn.commit()
        return cur.rowcount


def delete_notification(notif_id: int, user_id: str) -> bool:
    """删除通知"""
    with get_conn() as conn:
        cur = _execute(conn, "DELETE FROM notifications WHERE id=? AND user_id=?", (notif_id, user_id))
        conn.commit()
        return cur.rowcount > 0
