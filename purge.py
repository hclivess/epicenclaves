import os
import os.path

to_wipeout = ["db/auth.db", "db/map_data.db", "cookie_secret", "db/user_data.db"]


def delete(to_wipeout):
    for file in to_wipeout:
        try:
            print(f"Removing {file}")
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        except Exception as e:
            print(f"Exception: {e}")

delete(to_wipeout)