import math
import os
import random
from hashlib import blake2b

if not os.path.exists("db"):
    os.mkdir("db")

def hashify(data):
    hashified = blake2b(data.encode(), digest_size=15).hexdigest()
    return hashified


def has_resources(user_data, cost):
    ingredients = user_data.get("ingredients", {})
    for resource, amount in cost.get("ingredients", {}).items():
        if ingredients.get(resource, 0) < amount:
            return False
    return True


def has_item_equipped(data, item_type):
    items = data.get("equipped", [])

    for item in items:
        if item.get("type") == item_type:
            return True

    return False


def get_user(user, user_data_dict, get_construction=True):
    #print(user_data_dict)
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
    #print("update_user_data", user, updated_values)

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
    key = f"{construction_coordinates['x_pos']},{construction_coordinates['y_pos']}"

    if user not in user_data_dict:
        print("User not found")
        return

    user_data = user_data_dict[user]

    if "construction" in user_data and isinstance(user_data["construction"], dict):
        user_data["construction"].pop(key, None)


def get_values(entry):
    return list(entry.values())[0]


def calculate_level(min_level, max_level, bias=0):
    # Ensure min_level and max_level are integers
    min_level = int(min_level)
    max_level = int(max_level)

    # If min_level is greater than or equal to max_level, return min_level
    if min_level >= max_level:
        print("log level roll", min_level, max_level, min_level)
        return min_level

    # Generate a random value between 0 and 1
    random_value = random.random()

    # Adjust the random value with a bias factor to skew the distribution
    if bias != 0:
        biased_random_value = random_value ** (1 / bias)
    else:
        biased_random_value = random_value

    # Calculate the logarithmic distribution
    log_min = math.log(max(min_level, 1))
    log_max = math.log(max_level)
    log_result = log_min + biased_random_value * (log_max - log_min)
    result = int(round(math.exp(log_result)))

    # Ensure the result is within the allowed range
    result = max(min_level, min(result, max_level))

    print("log level roll", min_level, max_level, result)
    return result