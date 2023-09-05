import random

from map import save_map_data

import random

def spawn_herd(entity_class, probability, mapdb, size=101, max_entities=None, herd_size=5, max_offset=5):
    generated_count = 0

    while generated_count < max_entities:
        x_pos = random.randint(1, size)
        y_pos = random.randint(1, size)

        coord_key = f"{x_pos},{y_pos}"
        if coord_key in mapdb:
            # Skip this location as there's already an entity there
            continue

        if random.random() <= probability:
            # Generate a herd of entities
            for _ in range(herd_size):
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

                data = {"type": entity_class.__name__}
                data.update(additional_entity_data)
                print(f"Generating {data} on {x_pos}, {y_pos}")
                save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)
                generated_count += 1

                if generated_count >= max_entities:
                    return




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
