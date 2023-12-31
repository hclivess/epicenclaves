from backend import update_user_data

from backend import update_user_data


def move(user, entry, axis_limit, user_data, users_dict, map_dict):
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
        other_axis_key = "y_pos" if axis_key == "x_pos" else "x_pos"
        other_axis_value = user_data.get(other_axis_key, 0)

        coord_key = f"{new_pos},{other_axis_value}" if axis_key == "x_pos" else f"{other_axis_value},{new_pos}"
        current_coord_key = f"{user_data.get(axis_key, 0)},{other_axis_value}" if axis_key == "x_pos" else f"{other_axis_value},{user_data.get(axis_key, 0)}"

        current_control = map_dict.get(current_coord_key, {}).get("control")
        new_spot_control = map_dict.get(coord_key, {}).get("control")

        if not user_data.get("alive"):
            return_message["message"] = "Cannot move while dead"

        elif user_data.get("action_points", 0) <= 0:
            return_message["message"] = "Out of action points"

        elif new_pos < 1 or new_pos > axis_limit:
            return_message["message"] = "Out of bounds"

        elif map_dict.get(coord_key, {}).get("type") == "wall":
            return_message["message"] = "Cannot move into a wall"

        elif current_control and current_control != user and new_spot_control and new_spot_control != user:
            return_message["message"] = "Cannot move deeper into enemy territory"

        else:
            return_message["success"] = True
            return_message["message"] = "Moved successfully"

            update_user_data(
                user,
                {axis_key: new_pos, "action_points": user_data["action_points"] - 1},
                users_dict,
            )

    return return_message

