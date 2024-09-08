import math
import random

from map import get_map_at_coords


def process_outpost_attacks(mapdb, usersdb, league):
    coords_to_process = list(mapdb[league].keys())

    for coord in coords_to_process:
        if coord in mapdb[league]:  # Check if the coord still exists
            tile_data = mapdb[league][coord]
            if tile_data.get("type") == "outpost":
                attack_enemy_siege(mapdb, usersdb, league, coord)


def attack_enemy_siege(mapdb, usersdb, league, outpost_coord):
    x, y = map(int, outpost_coord.split(','))
    outpost_owner = mapdb[league][outpost_coord]["control"]

    targetable_sieges = []
    for i in range(x - 30, x + 31):
        for j in range(y - 30, y + 31):
            if math.sqrt((i - x)**2 + (j - y)**2) <= 30:
                siege_coord = f"{i},{j}"
                siege_tile = get_map_at_coords(i, j, mapdb[league])
                if siege_tile:
                    siege_tile = siege_tile[siege_coord]  # Unwrap the tile data
                    if siege_tile.get("type") == "siege" and siege_tile["control"] != outpost_owner:
                        targetable_sieges.append(siege_coord)

    if targetable_sieges:
        target_coord = random.choice(targetable_sieges)
        damage_siege(mapdb, usersdb, league, target_coord)


def damage_siege(mapdb, usersdb, league, siege_coord):
    if siege_coord in mapdb[league]:  # Check if the siege still exists
        siege = mapdb[league][siege_coord]

        # If HP is not set, initialize it to 250 (as per the Siege class in the original code)
        if "hp" not in siege:
            siege["hp"] = 250

        siege["hp"] -= 1

        if siege["hp"] <= 0:
            del mapdb[league][siege_coord]
            owner = siege["control"]
            if owner in usersdb[league]:
                user_data = usersdb[league][owner]
                if "construction" in user_data and siege_coord in user_data["construction"]:
                    del user_data["construction"][siege_coord]
        else:
            mapdb[league][siege_coord] = siege
