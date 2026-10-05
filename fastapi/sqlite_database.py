import json
import sqlite3
import uuid
from datetime import UTC, datetime


def init_and_seed_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            user_roles TEXT NOT NULL,
            email TEXT UNIQUE,
            full_name TEXT,
            hashed_password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction (
            prediction_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            text TEXT NOT NULL,
            intention TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES user(user_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM user;")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        admin_id = str(uuid.uuid4())
        normal_id = str(uuid.uuid4())

        now = datetime.now(UTC).isoformat()
        roles_admin = json.dumps(["default", "admin"])
        roles_normal = json.dumps(["default"])

        # Password: johndoe123
        cursor.execute(
            """
            INSERT INTO user (user_id, username, user_roles, email, full_name, hashed_password)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                admin_id,
                "johndoe",
                roles_admin,
                "johndoe@example.com",
                "John Doe",
                "$argon2id$v=19$m=65536,t=3,p=4$hjFEK9IfqxvgWuosbDlLNg$WXciJIpMfKc67ZOdM7R7QlZD85dbJ9hqbVa5Ch6feSU",
            ),
        )

        # Password: janedoe123
        cursor.execute(
            """
            INSERT INTO user (user_id, username, user_roles, email, full_name, hashed_password)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                normal_id,
                "janedoe",
                roles_normal,
                "janedoe@example.com",
                "Jane Doe",
                "$argon2id$v=19$m=65536,t=3,p=4$/a2StR3qmNBph8Ld/MHBhA$4KFVOj5121NExX6jrYSwZAHv0XzD6pH1ZB7JS/6d+QY",
            ),
        )

        cursor.execute(
            """
            INSERT INTO prediction (prediction_id, owner_id, text, intention, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                admin_id,
                "Cancelar minha assinatura",
                "cancel_subscription",
                now,
            ),
        )

        cursor.execute(
            """
            INSERT INTO prediction (prediction_id, owner_id, text, intention, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                normal_id,
                "Estou tendo problemas para acessar a plataforma",
                "Software bug",
                now,
            ),
        )

    conn.commit()
    conn.close()
