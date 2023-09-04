import os
import random
import string
from sqlite import hash_password, users_db

def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def auth_cookie_get():
    filename = "cookie_secret"
    create_directory_if_not_exists(filename)

    if not os.path.exists(filename):
        cookie_secret = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30))
        with open(filename, "w") as infile:
            infile.write(cookie_secret)
    else:
        with open(filename, "r") as infile:
            cookie_secret = infile.read()

    return cookie_secret

def auth_login_validate(user, password):
    with users_db:
        cursor = users_db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND passhash = ?", (user, hash_password(password)))
        result = cursor.fetchall()

    return bool(result)

def auth_add_user(user, password):
    with users_db:
        cursor = users_db.cursor()
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user, hash_password(password)))
        users_db.commit()

def auth_exists_user(user):
    with users_db:
        cursor = users_db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
        result = cursor.fetchall()

    return bool(result)

def auth_check_users_db():
    with users_db:
        cursor = users_db.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (username STRING PRIMARY KEY, passhash STRING)")
        users_db.commit()
