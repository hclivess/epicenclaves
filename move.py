from backend import update_user_data


def move(user, entry, axis_limit, user_data, users_dict):
    return_message = {"success": False, "message": None}
    move_map = {
        "left": (-1, "x_pos"),
        "right": (1, "x_pos"),
        "down": (1, "y_pos"),
        "up": (-1, "y_pos"),
    }

    if entry in move_map:
        direction, axis_key = move_map[entry]
        new_pos = user_data.get(axis_key, 0) + direction

        if not user_data.get("alive"):
            return_message["message"] = "Cannot move while dead"

        elif user_data.get("action_points", 0) <= 0:
            return_message["message"] = "Out of action points"

        elif new_pos < 1 or new_pos > axis_limit:
            return_message["message"] = "Out of bounds"

        else:
            return_message["success"] = True
            return_message["message"] = "Moved successfully"

            update_user_data(
                user,
                {axis_key: new_pos, "action_points": user_data["action_points"] - 1},
                users_dict,
            )

    return return_message
