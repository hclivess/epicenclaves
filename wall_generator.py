import random


def save_map_data(map_data_dict, x_pos, y_pos, data):
    # Use a string coordinate key like 'x,y'
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data


def would_create_closed_space(x, y, mapdb):
    neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    return all(mapdb.get((nx, ny)) is not None for nx, ny in neighbors)


def spawn_wall(entity_class, probability, mapdb, start_x=1, start_y=1, size=101, every=10, max_entities=None):
    generated_count = 0
    entity_instance = entity_class()

    additional_entity_data = {
        "type": getattr(entity_instance, "type", entity_class.__name__),
    }

    while generated_count < max_entities or max_entities is None:
        if random.random() <= probability:
            x_pos, y_pos = random.randint(start_x, size), random.randint(start_y, size)
            wall_length = random.randint(10, 50)  # For example, random length between 10 and 50

            for _ in range(wall_length):
                if would_create_closed_space(x_pos, y_pos, mapdb):
                    break

                data = {"type": entity_class.__name__}
                data.update(additional_entity_data)
                save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)

                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(directions)

                for dx, dy in directions:
                    new_x, new_y = x_pos + dx, y_pos + dy
                    if 0 < new_x < size and 0 < new_y < size and (new_x, new_y) not in mapdb:
                        x_pos, y_pos = new_x, new_y
                        break

            generated_count += 1


class Wall:
    pass  # Replace with actual implementation


# Dummy database for testing
mapdb = {}

spawn_wall(Wall, 0.5, mapdb, max_entities=20)

print(mapdb)
