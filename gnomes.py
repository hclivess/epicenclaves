import random

def move_gnomes(mapdb, league):
    gnomes_to_move = {}
    new_positions = {}

    # Identify all gnomes and their potential new positions
    for coord, tile in mapdb[league].items():
        if tile['type'] == 'gnomes':
            x, y = map(int, coord.split(','))
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            new_x = max(0, x + dx)
            new_y = max(0, y + dy)
            new_coord = f"{new_x},{new_y}"
            gnomes_to_move[coord] = new_coord

    # Move gnomes to their new positions
    for old_coord, new_coord in gnomes_to_move.items():
        if new_coord not in mapdb[league] and new_coord not in new_positions:
            new_positions[new_coord] = mapdb[league][old_coord]
            del mapdb[league][old_coord]

            # Invalidate chunks for both old and new positions
            old_x, old_y = map(int, old_coord.split(','))
            new_x, new_y = map(int, new_coord.split(','))
        else:
            # If the new position is occupied, keep the gnome in its original position
            new_positions[old_coord] = mapdb[league][old_coord]

    # Update the map with the new gnome positions
    mapdb[league].update(new_positions)