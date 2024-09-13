import random


def move_gnomes(mapdb, league):
    gnomes_to_move = {}
    new_positions = {}
    original_gnome_count = 0

    # First, identify all gnomes and their potential new positions
    for coord, tile in mapdb[league].items():
        if tile['type'] == 'gnomes':
            original_gnome_count += 1
            x, y = map(int, coord.split(','))
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            new_x, new_y = x + dx, y + dy
            new_coord = f"{new_x},{new_y}"
            gnomes_to_move[coord] = new_coord

    # Then, move gnomes to their new positions
    for old_coord, new_coord in gnomes_to_move.items():
        if new_coord not in mapdb[league] and new_coord not in new_positions:
            new_positions[new_coord] = {"role": "scenery", "type": "gnomes", "biome": "gnomes"}
        else:
            # If the new position is occupied or another gnome is moving there,
            # keep the gnome in its original position
            new_positions[old_coord] = mapdb[league][old_coord]

    # Update the map with the new gnome positions
    for coord in gnomes_to_move.keys():
        if coord not in new_positions:
            del mapdb[league][coord]

    mapdb[league].update(new_positions)

    print(f"Moved gnomes in {league}")
    print(f"Original gnome count: {original_gnome_count}")
    print(f"New gnome count: {len(new_positions)}")

    # Sanity check
    if len(new_positions) > original_gnome_count:
        print("WARNING: Gnome count increased! This should not happen.")
    elif len(new_positions) < original_gnome_count:
        print(f"Gnome count decreased by {original_gnome_count - len(new_positions)}")