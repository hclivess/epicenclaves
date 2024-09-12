from backend import update_user_data

def drag_player(target, direction, league, usersdb, mapdb, MAX_SIZE):
    target_data = usersdb[league].get(target)
    if not target_data:
        return f"Player {target} not found.", None, None

    if target_data.get("hp", 0) > 0:
        return f"Player {target} is not dead and cannot be dragged.", None, None

    dx, dy = 0, 0
    if direction == "up":
        dy = -1
    elif direction == "down":
        dy = 1
    elif direction == "left":
        dx = -1
    elif direction == "right":
        dx = 1
    else:
        return f"Invalid direction: {direction}", None, None

    target_x, target_y = target_data["x_pos"], target_data["y_pos"]
    new_x, new_y = target_x + dx, target_y + dy

    # Check if the new position is within the map boundaries
    if not (0 <= new_x < MAX_SIZE and 0 <= new_y < MAX_SIZE):
        return "Cannot drag the player outside the map boundaries.", None, None

    # Update the dragged player's position
    update_user_data(target, {"x_pos": new_x, "y_pos": new_y}, usersdb[league])

    return f"Dragged player {target} {direction}.", new_x, new_y