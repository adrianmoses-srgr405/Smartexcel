import sys
import subprocess
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_postgresql(password: str):
    # Step 1: Connect as postgres superuser to ensure role and database exist
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="postgres",
            password=password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check and create/alter smartAdmin role
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'smartAdmin'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE ROLE \"smartAdmin\" WITH LOGIN CREATEDB SUPERUSER PASSWORD %s;", (password,))
            print("[INFO] Role 'smartAdmin' created successfully.")
        else:
            cur.execute(f"ALTER ROLE \"smartAdmin\" WITH LOGIN CREATEDB SUPERUSER PASSWORD %s;", (password,))
            print("[INFO] Role 'smartAdmin' updated with credentials.")

        # Check and create smart_excel database
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'smart_excel'")
        db_exists = cur.fetchone()
        if not db_exists:
            cur.execute("CREATE DATABASE smart_excel OWNER \"smartAdmin\";")
            print("[INFO] Database 'smart_excel' created with owner 'smartAdmin'.")
        else:
            cur.execute("ALTER DATABASE smart_excel OWNER TO \"smartAdmin\";")
            print("[INFO] Database 'smart_excel' already exists. Ownership confirmed.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR during postgres admin setup]: {e}")
        return False

    # Step 2: Test connecting directly as smartAdmin to smart_excel
    try:
        test_conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="smartAdmin",
            password=password,
            database="smart_excel"
        )
        test_cur = test_conn.cursor()
        test_cur.execute("SELECT version();")
        ver = test_cur.fetchone()[0]
        print(f"[SUCCESS] Connected to smart_excel as smartAdmin! PostgreSQL Version: {ver.split(',')[0]}")
        test_cur.close()
        test_conn.close()
        return True
    except Exception as e:
        print(f"[ERROR connecting as smartAdmin]: {e}")
        return False

if __name__ == "__main__":
    from app.core.config import settings
    p = os.environ.get("DB_PASSWORD") or settings.DB_PASSWORD
    if not p:
        print("[ERROR] DB_PASSWORD is not set in environment.")
        sys.exit(1)
    ok = setup_postgresql(p)
    if not ok:
        sys.exit(1)

