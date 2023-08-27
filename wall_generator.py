import random

def save_map_data(map_data_dict, x_pos, y_pos, data):
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data

def would_create_closed_space(x, y, mapdb):
    neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    diagonals = [(x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)]
    return all(mapdb.get(f"{nx},{ny}") is not None for nx, ny in neighbors) or all(mapdb.get(f"{dx},{dy}") is not None for dx, dy in diagonals)

def count_neighboring_walls(x, y, mapdb):
    neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    return sum(1 for nx, ny in neighbors if mapdb.get(f"{nx},{ny}") is not None)

def spawn_wall(entity_class, probability, mapdb, start_x=1, start_y=1, size=101, every=10, max_entities=None):
    generated_count = 0
    entity_instance = entity_class()
    additional_entity_data = {
        "type": getattr(entity_instance, "type", entity_class.__name__),
    }

    while generated_count < max_entities or max_entities is None:
        if random.random() <= probability:
            x_pos, y_pos = random.randint(start_x, size), random.randint(start_y, size)
            wall_length = random.randint(10, 50)

            for _ in range(wall_length):
                if would_create_closed_space(x_pos, y_pos, mapdb):
                    break
                if count_neighboring_walls(x_pos, y_pos, mapdb) > 1:
                    break

                candidate_positions = []

                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(directions)

                for dx, dy in directions:
                    new_x, new_y = x_pos + dx, y_pos + dy
                    if 0 < new_x < size and 0 < new_y < size and f"{new_x},{new_y}" not in mapdb:
                        if count_neighboring_walls(new_x, new_y, mapdb) <= 1 and not would_create_closed_space(new_x, new_y, mapdb):
                            candidate_positions.append((new_x, new_y))

                if not candidate_positions:
                    break

                x_pos, y_pos = random.choice(candidate_positions)

                data = {"type": entity_class.__name__}
                data.update(additional_entity_data)
                save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)

            generated_count += 1
