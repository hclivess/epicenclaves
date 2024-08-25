import os
from hashlib import blake2b

if not os.path.exists("db"):
    os.mkdir("db")

from threading import Lock

# Initialize locks
user_lock = Lock()
map_lock = Lock()


def hashify(data):
    hashified = blake2b(data.encode(), digest_size=15).hexdigest()
    return hashified


def has_resources(user_data, cost):
    for resource, amount in cost.items():
        if user_data.get(resource, 0) < amount:
            return False
    return True


def has_item_equipped(data, item_type):
    items = data.get("equipped", [])

    for item in items:
        if item.get("type") == item_type:
            return True

    return False


def get_user(user, user_data_dict, get_construction=True):
    if user not in user_data_dict:
        print(f"User {user} not found in the dictionary. (backend.py)")
        return None

    user_entry = user_data_dict[user]

    # Extract x_pos, y_pos, and other data from user_entry
    x_pos = user_entry.get("x_pos", 0)
    y_pos = user_entry.get("y_pos", 0)
    data = {
        k: v
        for k, v in user_entry.items()
        if k not in ["x_pos", "y_pos", "construction"]
    }

    # get the "construction" data only if get_construction is True
    construction = (
        user_entry["construction"]
        if get_construction and "construction" in user_entry
        else {}
    )

    user_data = {
        user: {"x_pos": x_pos, "y_pos": y_pos, **data, "construction": construction}
    }

    return user_data

def update_user_data(user, updated_values, user_data_dict):
    with user_lock:
        print("update_user_data", user, updated_values)

        if user not in user_data_dict:
            print("User not found")
            return

        user_entry = user_data_dict[user]

        for key, value in updated_values.items():
            if value is None:
                continue  # Skip keys with None value to preserve existing data

            if (
                key == "construction"
                and "construction" in user_entry
                and isinstance(value, dict)
            ):
                for coord, construction_info in value.items():
                    user_entry["construction"][coord] = construction_info
            else:
                user_entry[key] = value


def remove_from_user(user, construction_coordinates, user_data_dict):
    with user_lock:
        key = f"{construction_coordinates['x_pos']},{construction_coordinates['y_pos']}"

        if user not in user_data_dict:
            print("User not found")
            return

        user_data = user_data_dict[user]

        if "construction" in user_data and isinstance(user_data["construction"], dict):
            user_data["construction"].pop(key, None)


def get_values(entry):
    return list(entry.values())[0]


