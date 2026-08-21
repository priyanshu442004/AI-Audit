import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

DB_URL = os.environ.get("DATABASE_URL")

_pool = None

def get_connection():
    global _pool
    if not DB_URL:
        raise ValueError("DATABASE_URL is not set in environment variables.")
    if _pool is None:
        _pool = ThreadedConnectionPool(1, 20, DB_URL)
    try:
        conn = _pool.getconn()
        if conn and conn.closed != 0:
            try:
                _pool.closeall()
            except Exception:
                pass
            _pool = ThreadedConnectionPool(1, 20, DB_URL)
            conn = _pool.getconn()
        return conn
    except Exception:
        try:
            if _pool:
                _pool.closeall()
        except Exception:
            pass
        _pool = ThreadedConnectionPool(1, 20, DB_URL)
        return _pool.getconn()

def put_connection(conn):
    global _pool
    if _pool and conn:
        try:
            if conn.closed == 0:
                _pool.putconn(conn)
            else:
                _pool.putconn(conn, close=True)
        except Exception:
            pass

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS s3_uploaded_files (
                id SERIAL PRIMARY KEY,
                role VARCHAR(50) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                s3_key VARCHAR(500) NOT NULL,
                s3_url VARCHAR(1000) NOT NULL,
                row_count INTEGER DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                entity VARCHAR(50) DEFAULT 'ISPL',
                process VARCHAR(50) DEFAULT 'P2P'
            );
        """)
        cur.execute("""
            ALTER TABLE s3_uploaded_files ADD COLUMN IF NOT EXISTS entity VARCHAR(50) DEFAULT 'ISPL';
        """)
        cur.execute("""
            ALTER TABLE s3_uploaded_files ADD COLUMN IF NOT EXISTS process VARCHAR(50) DEFAULT 'P2P';
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action VARCHAR(255) NOT NULL,
                filename VARCHAR(500),
                user_action VARCHAR(255) NOT NULL,
                last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) DEFAULT 'Admin User',
                profile_pic_url VARCHAR(1000) DEFAULT '',
                mobile_number VARCHAR(50) DEFAULT '',
                email VARCHAR(255) UNIQUE DEFAULT 'admin@ikio.com',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            INSERT INTO user_profile (id, name, profile_pic_url, mobile_number, email)
            VALUES (1, 'Admin User', '', '+91 99999 99999', 'admin@ikio.com')
            ON CONFLICT (id) DO NOTHING;
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)

def add_uploaded_file(role: str, filename: str, s3_key: str, s3_url: str, row_count: int, entity: str = "ISPL", process: str = "P2P"):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            INSERT INTO s3_uploaded_files (role, filename, s3_key, s3_url, row_count, entity, process)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, role, filename, s3_key, s3_url, row_count, uploaded_at, entity, process;
        """, (role, filename, s3_key, s3_url, row_count, entity, process))
        row = cur.fetchone()
        conn.commit()
        return dict(row)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)

def get_active_files(entity: str = "ITL", process: str = "P2P"):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, role, filename, s3_key, s3_url, row_count, uploaded_at, entity, process
            FROM s3_uploaded_files
            WHERE is_deleted = FALSE AND UPPER(entity) = UPPER(%s) AND UPPER(process) = UPPER(%s)
            ORDER BY uploaded_at DESC;
        """, (entity, process))
        rows = cur.fetchall()
        if not rows and process.upper() == "P2P":
            # Fallback to any active P2P files if entity specific files not uploaded yet
            cur.execute("""
                SELECT id, role, filename, s3_key, s3_url, row_count, uploaded_at, entity, process
                FROM s3_uploaded_files
                WHERE is_deleted = FALSE AND UPPER(process) = 'P2P'
                ORDER BY uploaded_at DESC;
            """)
            rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        raise e
    finally:
        cur.close()
        put_connection(conn)

def get_file_by_id(file_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, role, filename, s3_key, s3_url, row_count, uploaded_at, is_deleted, entity, process
            FROM s3_uploaded_files
            WHERE id = %s;
        """, (file_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        raise e
    finally:
        cur.close()
        put_connection(conn)

def delete_file(file_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE s3_uploaded_files
            SET is_deleted = TRUE
            WHERE id = %s;
        """, (file_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)

def delete_all_files(entity: str = "ISPL", process: str = "P2P"):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE s3_uploaded_files
            SET is_deleted = TRUE
            WHERE is_deleted = FALSE AND UPPER(entity) = UPPER(%s) AND UPPER(process) = UPPER(%s);
        """, (entity, process))
        count = cur.rowcount
        conn.commit()
        return count
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)

def replace_file(file_id: int, filename: str, s3_key: str, s3_url: str, row_count: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            UPDATE s3_uploaded_files
            SET filename = %s, s3_key = %s, s3_url = %s, row_count = %s, is_deleted = FALSE, uploaded_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, role, filename, s3_key, s3_url, row_count, uploaded_at, entity, process;
        """, (filename, s3_key, s3_url, row_count, file_id))
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)


def add_audit_log(action: str, filename: str | None, user_action: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO audit_logs (action, filename, user_action, last_fetched)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (action, filename, user_action))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Failed to add audit log: {e}")
    finally:
        cur.close()
        put_connection(conn)


def get_audit_logs():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, timestamp, action, filename, user_action, last_fetched
            FROM audit_logs
            ORDER BY timestamp DESC
            LIMIT 100;
        """)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Failed to get audit logs: {e}")
        return []
    finally:
        cur.close()
        put_connection(conn)


def get_user_profile():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, name, profile_pic_url, mobile_number, email, updated_at
            FROM user_profile
            WHERE id = 1;
        """)
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO user_profile (id, name, profile_pic_url, mobile_number, email)
                VALUES (1, 'Admin User', '', '+91 99999 99999', 'admin@ikio.com')
                ON CONFLICT (id) DO NOTHING;
            """)
            conn.commit()
            cur.execute("""
                SELECT id, name, profile_pic_url, mobile_number, email, updated_at
                FROM user_profile
                WHERE id = 1;
            """)
            row = cur.fetchone()
        return dict(row)
    except Exception as e:
        raise e
    finally:
        cur.close()
        put_connection(conn)


def update_user_profile(name: str, profile_pic_url: str | None, mobile_number: str, email: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if profile_pic_url is not None:
            cur.execute("""
                UPDATE user_profile
                SET name = %s, profile_pic_url = %s, mobile_number = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                RETURNING id, name, profile_pic_url, mobile_number, email, updated_at;
            """, (name, profile_pic_url, mobile_number, email))
        else:
            cur.execute("""
                UPDATE user_profile
                SET name = %s, mobile_number = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                RETURNING id, name, profile_pic_url, mobile_number, email, updated_at;
            """, (name, mobile_number, email))
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        put_connection(conn)

