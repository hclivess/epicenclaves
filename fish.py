from backend import update_user_data
from map import occupied_by, owned_by
import random

def fish_pond(user, user_data, usersdb, mapdb, fish_amount=1):
    # Check if the fishing spot is under the user's control
    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )
    if not under_control:
        return "You do not own this fishing spot"

    # Check if the user is on a water tile
    proper_tile = occupied_by(
        user_data["x_pos"], user_data["y_pos"], what="pond", mapdb=mapdb
    )
    if not proper_tile:
        return "Not on a pond tile"

    # Check if the user has enough action points
    if user_data["action_points"] < fish_amount:
        return "Not enough action points to fish"

    # Perform fishing with 50% success rate
    successful_attempts = 0
    for _ in range(fish_amount):
        if random.random() < 0.5:  # 50% chance of success
            successful_attempts += 1

    # Update user's data
    ingredients = user_data.get("ingredients", {})
    ingredients["fish"] = ingredients.get("fish", 0) + successful_attempts
    new_ap = user_data["action_points"] - fish_amount  # Deduct action points

    updated_values = {"action_points": new_ap, "ingredients": ingredients}
    update_user_data(
        user=user,
        updated_values=updated_values,
        user_data_dict=usersdb,
    )

    if successful_attempts > 0:
        return f"Fishing successful. You caught {successful_attempts} fish!"
    else:
        return "Fishing unsuccessful. Better luck next time!"