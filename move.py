from backend import update_user_data


def move_to(user, target_x, target_y, axis_limit, user_data, users_dict, map_dict):
    return_message = {"success": False, "message": None, "steps_taken": 0}

    current_x = user_data.get("x_pos", 0)
    current_y = user_data.get("y_pos", 0)

    # Calculate the distance
    dx = target_x - current_x
    dy = target_y - current_y
    distance = abs(dx) + abs(dy)  # Using Manhattan distance

    if not user_data.get("alive"):
        return_message["message"] = "Cannot move while dead"
    elif user_data.get("action_points", 0) < distance:
        return_message[
            "message"] = f"Not enough action points. Need {distance}, have {user_data.get('action_points', 0)}"
    elif target_x < 1 or target_x > axis_limit or target_y < 1 or target_y > axis_limit:
        return_message["message"] = "Target position is out of bounds"
    else:
        # Check the path
        x, y = current_x, current_y
        while x != target_x or y != target_y:
            next_x, next_y = x, y

            if x < target_x:
                next_x += 1
            elif x > target_x:
                next_x -= 1

            if y < target_y:
                next_y += 1
            elif y > target_y:
                next_y -= 1

            # Check for diagonal movement to rock
            if next_x != x and next_y != y:
                horizontal_key = f"{next_x},{y}"
                vertical_key = f"{x},{next_y}"
                diagonal_key = f"{next_x},{next_y}"

                horizontal_type = map_dict.get(horizontal_key, {}).get("type")
                vertical_type = map_dict.get(vertical_key, {}).get("type")
                diagonal_type = map_dict.get(diagonal_key, {}).get("type")

                if diagonal_type == "rock" and (horizontal_type == "rock" or vertical_type == "rock"):
                    return_message[
                        "message"] = f"Stopped at {x},{y}. Cannot move diagonally to a rock at {diagonal_key}"
                    break

            coord_key = f"{next_x},{next_y}"
            tile_data = map_dict.get(coord_key, {})
            tile_type = tile_data.get("type")
            tile_control = tile_data.get("control")

            if tile_type == "rock":
                return_message["message"] = f"Stopped at {x},{y}. Cannot move through a rock at {coord_key}"
                break
            elif tile_type == "palisade":
                if tile_control != user:
                    return_message[
                        "message"] = f"Stopped at {x},{y}. Cannot move through an enemy controlled palisade at {coord_key}"
                    break

            x, y = next_x, next_y
            return_message["steps_taken"] += 1

        # Check if any movement occurred
        if return_message["steps_taken"] > 0:
            return_message["success"] = True
            return_message["message"] = f"Moved to {x},{y}. Steps taken: {return_message['steps_taken']}"

            update_user_data(
                user,
                {"x_pos": x, "y_pos": y, "action_points": user_data["action_points"] - return_message["steps_taken"]},
                users_dict,
            )
        elif not return_message["message"]:
            return_message["message"] = "No movement occurred"

    return return_message

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
        new_spot_type = map_dict.get(coord_key, {}).get("type")

        if not user_data.get("alive"):
            return_message["message"] = "Cannot move while dead"
        elif user_data.get("action_points", 0) <= 0:
            return_message["message"] = "Out of action points"
        elif new_pos < 1 or new_pos > axis_limit:
            return_message["message"] = "Out of bounds"
        elif new_spot_type == "rock":
            return_message["message"] = "Cannot move into a rock"
        elif new_spot_type == "palisade" and map_dict[coord_key].get("control") != user:
            return_message["message"] = "Cannot move through an enemy palisade"
        elif current_control and current_control != user and new_spot_control and new_spot_control != user:
            return_message["message"] = "Cannot move from one enemy tile to another"
        else:
            return_message["success"] = True
            return_message["message"] = "Moved successfully"

            update_user_data(
                user,
                {axis_key: new_pos, "action_points": user_data["action_points"] - 1},
                users_dict,
            )

    return return_message