import random

def save_map_data(map_data_dict, x_pos, y_pos, data):
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data

def is_closed_space(x, y, mapdb):
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if dx == 0 and dy == 0:
                continue
            if mapdb.get(f"{x + dx},{y + dy}") is None:
                return False
    return True

def spawn_wall(entity_class, probability, mapdb, start_x=1, start_y=1, size=101, max_entities=20, wall_length=50):
    generated_count = 0
    entity_instance = entity_class()

    while generated_count < max_entities:
        if random.random() <= probability:
            x_pos, y_pos = random.randint(start_x, size), random.randint(start_y, size)
            current_wall = []

            for _ in range(wall_length):
                if is_closed_space(x_pos, y_pos, mapdb):
                    break

                candidate_positions = []
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(directions)

                for dx, dy in directions:
                    new_x, new_y = x_pos + dx, y_pos + dy
                    if 0 < new_x < size and 0 < new_y < size and f"{new_x},{new_y}" not in mapdb:
                        if not is_closed_space(new_x, new_y, mapdb):
                            candidate_positions.append((new_x, new_y))

                if not candidate_positions:
                    break

                x_pos, y_pos = random.choice(candidate_positions)
                current_wall.append((x_pos, y_pos))

            if all(not is_closed_space(x, y, mapdb) for x, y in current_wall):
                for x, y in current_wall:
                    data = {"type": entity_instance.type}
                    save_map_data(x_pos=x, y_pos=y, data=data, map_data_dict=mapdb)

                generated_count += 1