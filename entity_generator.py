from map import save_map_data
import random


import random

def spawn(entity_instance, probability, mapdb, level, size=101, max_entities=None, herd_size=15,
          herd_radius=5, herd_probability=0.5):
    total_entities = 0
    additional_entity_data = generate_additional_entity_data(entity_instance, level)
    total_tiles = size * size

    while True:
        if random.random() > probability:
            print("Spawn skipped due to low probability")
            break

        if max_entities is not None and total_entities >= max_entities:
            return

        if len(mapdb) >= total_tiles:
            print(f"No more empty tiles available ({len(mapdb)}/{total_tiles}).")
            return

        x_pos = random.randint(1, size)
        y_pos = random.randint(1, size)
        coord_key = f"{x_pos},{y_pos}"

        if coord_key in mapdb:
            continue

        if random.random() <= herd_probability:
            level_one_count = max(1, int(0.1 * herd_size))
            for idx in range(herd_size):
                if total_entities >= max_entities:
                    return
                effective_level = 1 if idx < level_one_count else level
                x_offset = random.randint(-herd_radius, herd_radius)
                y_offset = random.randint(-herd_radius, herd_radius)
                new_x = x_pos + x_offset
                new_y = y_pos + y_offset
                new_coord_key = f"{new_x},{new_y}"

                if 1 <= new_x <= size and 1 <= new_y <= size and new_coord_key not in mapdb:
                    data = {"type": entity_instance.type}
                    data.update(generate_additional_entity_data(entity_instance, effective_level))
                    print(f"Generating {data} on {new_x}, {new_y}")
                    save_map_data(x_pos=new_x, y_pos=new_y, data=data, map_data_dict=mapdb)
                    total_entities += 1
        else:
            data = {"type": entity_instance.type}
            data.update(additional_entity_data)
            print(f"Generating {data} on {x_pos}, {y_pos}")
            save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)
            total_entities += 1



def generate_additional_entity_data(entity_instance, level):
    return {
        "type": getattr(entity_instance, "type", entity_instance.type),
        **({"experience": entity_instance.experience * level} if hasattr(entity_instance, "experience") else {}),
        **({"armor": entity_instance.armor * level} if hasattr(entity_instance, "armor") else {}),
        **({"max_damage": entity_instance.max_damage * level} if hasattr(entity_instance, "max_damage") else {}),
        **({"role": entity_instance.role} if hasattr(entity_instance, "role") else {}),
        **({"level": level} if hasattr(entity_instance, "level") else {})
    }


def count_entities_of_type(mapdb, entity_type):
    return sum(1 for data in mapdb.values() if "type" in data and data["type"] == entity_type)
