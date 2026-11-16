
import sqlite3
from datetime import datetime

DATABASE = "chat_history.db"


def initialize_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            preference TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_message(session_id, role, content):

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO messages
        (session_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        session_id,
        role,
        content,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()


def get_history(session_id):

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    messages = cursor.fetchall()

    connection.close()

    return [
        {"role": role, "text": content}
        for role, content in messages
    ]

def clear_history(session_id):

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE session_id = ?
    """, (session_id,))

    connection.commit()
    connection.close()

def save_preference(session_id, preference):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO preferences (session_id, preference)
        VALUES (?, ?)
    """, (session_id, preference))

    connection.commit()
    connection.close()


def get_preferences(session_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT preference
        FROM preferences
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))

    preferences = cursor.fetchall()

    connection.close()

    return [item[0] for item in preferences]
def delete_preference(session_id, preference_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM preferences
        WHERE id = ? AND session_id = ?
    """, (preference_id, session_id))

    connection.commit()
    connection.close()


def clear_preferences(session_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM preferences
        WHERE session_id = ?
    """, (session_id,))

    connection.commit()
    connection.close()
def get_chat_sessions():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            session_id,
            (
                SELECT content
                FROM messages AS m2
                WHERE m2.session_id = m1.session_id
                ORDER BY id ASC
                LIMIT 1
            ) AS title,
            MAX(created_at) AS last_message
        FROM messages AS m1
        GROUP BY session_id
        ORDER BY MAX(id) DESC
    """)

    chats = cursor.fetchall()

    connection.close()

    return chats
# Delete one conversation
def delete_chat_session(session_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM messages WHERE session_id = ?",
        (session_id,)
    )

    connection.commit()
    connection.close()