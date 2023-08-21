from backend import owned_by, get_values, update_user_data, get_coords, update_map_data


def deploy_army(user, on_tile_map, usersdb, mapdb, user_data):
    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )

    if not under_control:
        return "You do not own this tile"

    if user_data["action_points"] < 1:
        return "Not enough action points to build"

    if not user_data.get("army_free") > 0:
        return "Not enough free army available"

    for entry in on_tile_map:
        """loop because only one structure is allowed per tile"""
        entry_cls = get_values(entry).get("cls")
        if entry_cls == "building":
            print("entry", entry)

            update_user_data(
                user,
                updated_values={
                    "army_free": user_data.get("army_free") - 1,
                    "army_deployed": user_data.get("army_deployed") + 1,
                    "action_points": user_data.get("action_points") - 1,
                },
                user_data_dict=usersdb,
            )

            # update garrison in acquired tiles
            player_pos = f"{user_data['x_pos']},{user_data['y_pos']}"
            old_tile = user_data["construction"][player_pos]
            old_tile["soldiers"] += 1
            update_user_data(
                user,
                updated_values={"construction": {player_pos: old_tile}},
                user_data_dict=usersdb,
            )
            # / update garrison in acquired tiles

            # Update map
            #key = get_coords(entry)
            #entry[key]["soldiers"] += 1
            updated_data = entry

            update_map_data(updated_data, mapdb)
            # / Update map

            return "Soldiers deployed"

    return "Army must be stationed on a building"
