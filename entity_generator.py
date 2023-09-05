from map import save_map_data
import random


def count_entities_of_type(mapdb, entity_type):
    # Count the total number of entities of a specific type in the map
    return sum(1 for data in mapdb.values() if "type" in data and data["type"] == entity_type)

def spawn_herd(entity_class, probability, mapdb, size=101, max_entities=50, herd_size=15, herd_radius=5):
    total_entities = count_entities_of_type(mapdb, entity_class.type)

    while total_entities < max_entities:
        x_pos = random.randint(1, size)
        y_pos = random.randint(1, size)

        coord_key = f"{x_pos},{y_pos}"
        if coord_key in mapdb:
            # Skip this location as there's already an entity there
            continue

        if random.random() <= probability:
            # Generate a herd of entities
            for _ in range(herd_size):
                if total_entities >= max_entities:
                    return  # Stop spawning if the total limit for this type is reached

                entity_instance = entity_class()

                additional_entity_data = {
                    "type": entity_class.type,
                    **({"role": entity_instance.role} if hasattr(entity_instance, "role") else {}),
                    **(
                        {"armor": entity_instance.armor}
                        if hasattr(entity_instance, "armor")
                        else {}
                    ),
                    **(
                        {"max_damage": entity_instance.max_damage}
                        if hasattr(entity_instance, "max_damage")
                        else {}
                    ),
                }

                # Generate positions within a radius around the initial position
                for _ in range(herd_radius):
                    x_offset = random.randint(-herd_radius, herd_radius)
                    y_offset = random.randint(-herd_radius, herd_radius)

                    new_x = x_pos + x_offset
                    new_y = y_pos + y_offset

                    new_coord_key = f"{new_x},{new_y}"

                    # Check if the new position is within the map boundaries and not occupied
                    if 1 <= new_x <= size and 1 <= new_y <= size and new_coord_key not in mapdb:
                        data = {"type": entity_class.type}
                        data.update(additional_entity_data)
                        print(f"Generating {data} on {new_x}, {new_y}")
                        save_map_data(x_pos=new_x, y_pos=new_y, data=data, map_data_dict=mapdb)
                        total_entities += 1


def spawn_entity(entity_class, probability, mapdb, start_x=1, start_y=1, size=101, every=10, max_entities=None):
    generated_count = 0
    entity_instance = entity_class()

    additional_entity_data = {
        "type": getattr(entity_instance, "type", entity_class.__name__),
        **({"role": entity_instance.role} if hasattr(entity_instance, "role") else {}),
        **(
            {"armor": entity_instance.armor}
            if hasattr(entity_instance, "armor")
            else {}
        ),
        **(
            {"max_damage": entity_instance.max_damage}
            if hasattr(entity_instance, "max_damage")
            else {}
        ),
    }

    for x_pos in range(start_x, size, every):
        for y_pos in range(start_y, size, every):
            if max_entities is not None and generated_count >= max_entities:
                return

            coord_key = f"{x_pos},{y_pos}"
            if coord_key in mapdb:
                continue

            if random.random() <= probability:
                data = {"type": entity_class.__name__}
                data.update(additional_entity_data)
                print(f"Generating {data} on {x_pos}, {y_pos}")
                save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)
                generated_count += 1
