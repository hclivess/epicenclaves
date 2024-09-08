import random

from map import is_surrounded_by, get_map_at_coords


def damage_palisade(mapdb, usersdb, league, palisade_coord):
    if palisade_coord in mapdb[league]:  # Check if the palisade still exists
        palisade = mapdb[league][palisade_coord]

        # If HP is not set, initialize it to 100
        if "hp" not in palisade:
            palisade["hp"] = 100

        palisade["hp"] -= 1

        if palisade["hp"] <= 0:
            del mapdb[league][palisade_coord]
            owner = palisade["control"]
            if owner in usersdb[league]:
                user_data = usersdb[league][owner]
                if "construction" in user_data and palisade_coord in user_data["construction"]:
                    del user_data["construction"][palisade_coord]
        else:
            mapdb[league][palisade_coord] = palisade


def check_surrounding_palisades(mapdb, usersdb, league, siege_coord):
    x, y = map(int, siege_coord.split(','))
    siege_owner = mapdb[league][siege_coord]["control"]

    if is_surrounded_by(x, y, "palisade", mapdb[league], diameter=2):
        targetable_palisades = []
        for i in range(x - 2, x + 3):
            for j in range(y - 2, y + 3):
                adj_coord = f"{i},{j}"
                adj_tile = get_map_at_coords(i, j, mapdb[league])
                if adj_tile:
                    adj_tile = adj_tile[adj_coord]  # Unwrap the tile data
                    if adj_tile.get("type") == "palisade" and adj_tile["control"] != siege_owner:
                        targetable_palisades.append(adj_coord)

        if targetable_palisades:
            target_coord = random.choice(targetable_palisades)
            damage_palisade(mapdb, usersdb, league, target_coord)


def process_siege_attacks(mapdb, usersdb, league):
    # Create a list of coordinates to process
    coords_to_process = list(mapdb[league].keys())

    for coord in coords_to_process:
        if coord in mapdb[league]:  # Check if the coord still exists
            tile_data = mapdb[league][coord]
            if tile_data.get("type") == "siege":
                check_surrounding_palisades(mapdb, usersdb, league, coord)


