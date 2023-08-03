import os
import os.path

to_wipeout = ["users.db", "map_data.db", "cookie_secret", "user_data.db"]


def delete(to_wipeout):
    for file in to_wipeout:
        print(f"Removing {file}")
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")

delete(to_wipeout)