from map import occupied_by, owned_by, remove_from_map
from backend import update_user_data

def demolish(user, user_data, usersdb, mapdb):
    # Check if the user owns the building on the current tile
    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )
    if not under_control:
        return "You do not own this building"

    # Check if there is a building on the current tile
    proper_tile = occupied_by(
        user_data["x_pos"], user_data["y_pos"], what="building", mapdb=mapdb, method="role"
    )
    if not proper_tile:
        return "Not on a building tile"

    # Fetch the specific tile data from the map database
    coord = f"{user_data['x_pos']},{user_data['y_pos']}"
    tile_data = mapdb.get(coord)

    if not tile_data or "building" not in tile_data["role"]:
        return "No building to demolish here"

    # Get the building type for confirmation
    building_type = tile_data["type"]

    # Remove the building data from the map using remove_from_map function
    remove_from_map(coord, building_type, mapdb)

    # Update the user's construction data
    user_construction = user_data.get("construction", {})
    if coord in user_construction:
        del user_construction[coord]
        update_user_data(user=user, updated_values={"construction": user_construction}, user_data_dict=usersdb)

    return f"The {building_type} has been demolished."