import os
import sqlite3
from hashlib import blake2b

from map import create_map_database
from user import create_users_db

if not os.path.exists("db"):
    os.mkdir("db")
users_db = sqlite3.connect("db/auth.db")
users_db_cursor = users_db.cursor()


def update_turn(turn_value, league="game"):
    # Connect to the SQLite database
    db_path = os.path.join('db', 'game_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the 'turn' value in the 'game' table
    cursor.execute(f'''
        UPDATE {league}
        SET turn = ?
    ''', (turn_value,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def hash_password(password):
    salt = "vGY13MMUH4khKGscQOOg"
    passhash = blake2b(digest_size=30)
    passhash.update((password + salt).encode())
    return passhash.hexdigest()


class SQLiteConnectionPool:
    def __init__(self, db_name):
        self.db_name = db_name
        self.pool = []

    def get_connection(self):
        if self.pool:
            return self.pool.pop()
        else:
            return sqlite3.connect(self.db_name)

    def return_connection(self, conn):
        self.pool.append(conn)


# Initialize a connection pool
conn_pool = SQLiteConnectionPool("db/map_data.db")


def init_databases():
    map_exists = os.path.exists("db/map_data.db")
    user_exists = os.path.exists("db/user_data.db")

    if not map_exists:
        create_map_database()
    if not user_exists:
        create_users_db()

    return {"map_exists": map_exists}
