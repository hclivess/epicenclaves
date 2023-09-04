import os
import sqlite3
from hashlib import blake2b


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


create_directory_if_not_exists("db")

with sqlite3.connect("db/auth.db") as users_db:
    users_db_cursor = users_db.cursor()


def create_game_database():
    # Create the 'db' directory if it doesn't exist
    create_directory_if_not_exists('db')

    # Connect to the SQLite database
    db_path = os.path.join('db', 'game_data.db')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Create the 'game' table with 'turn' column and insert default value
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game (
                turn INTEGER DEFAULT 0
            )
        ''')


def update_turn(turn_value):
    # Connect to the SQLite database
    db_path = os.path.join('db', 'game_data.db')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Update the 'turn' value in the 'game' table
        cursor.execute('''
            UPDATE game
            SET turn = ?
        ''', (turn_value,))


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
