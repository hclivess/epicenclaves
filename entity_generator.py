from map import save_map_data
import random
import importlib

# Import all entities from a separate module
entities = importlib.import_module('entities')


def spawn_all_entities(mapdb):
    # Get all classes from the entities module that have a 'type' attribute
    entity_classes = [cls for name, cls in entities.__dict__.items() if isinstance(cls, type) and hasattr(cls, 'type')]

    for entity_class in entity_classes:
        entity_instance = entity_class()
        spawn(
            entity_instance=entity_instance,
            probability=getattr(entity_instance, 'probability', 1),
            mapdb=mapdb,
            level=getattr(entity_instance, 'level', 1),
            size=getattr(entity_instance, 'size', 101),
            max_entities=getattr(entity_instance, 'max_entities', None),
            max_entities_total=getattr(entity_instance, 'max_entities_total', None),
            herd_probability=getattr(entity_instance, 'herd_probability', 0.5)
        )


def spawn(entity_instance, probability, mapdb, level, size=101, max_entities=None, max_entities_total=None,
          herd_size=15, herd_radius=5, herd_probability=0.5):
    total_entities = 0
    additional_entity_data = generate_additional_entity_data(entity_instance, level)
    total_tiles = size * size

    # Count existing entities on the map
    existing_entities = sum(1 for value in mapdb.values() if value.get('type') == entity_instance.type)

    print(f"Attempting to spawn {entity_instance.type} entities:")
    print(f"  - Probability: {probability}")
    print(f"  - Max entities per spawn: {max_entities if max_entities is not None else 'Unlimited'}")
    print(f"  - Max total entities: {max_entities_total if max_entities_total is not None else 'Unlimited'}")
    print(f"  - Current entities on map: {existing_entities}")
    print(f"  - Map size: {size}x{size}")

    while True:
        if random.random() > probability:
            print(f"Spawn attempt for {entity_instance.type} skipped due to low probability ({probability})")
            break

        if max_entities is not None and total_entities >= max_entities:
            print(f"Reached maximum entities per spawn ({max_entities}) for {entity_instance.type}")
            return

        if max_entities_total is not None and existing_entities + total_entities >= max_entities_total:
            print(f"Reached maximum total entities ({max_entities_total}) for {entity_instance.type}")
            return

        if len(mapdb) >= total_tiles:
            print(f"No more empty tiles available ({len(mapdb)}/{total_tiles}) for {entity_instance.type}")
            return

        x_pos = random.randint(1, size)
        y_pos = random.randint(1, size)
        coord_key = f"{x_pos},{y_pos}"

        if coord_key in mapdb:
            print(f"Tile {coord_key} is occupied, trying another location for {entity_instance.type}")
            continue

        if random.random() <= herd_probability:
            print(f"Attempting to spawn a herd of {entity_instance.type}")
            level_one_count = max(1, int(0.1 * herd_size))
            herd_spawned = 0
            for idx in range(herd_size):
                if max_entities is not None and total_entities >= max_entities:
                    print(
                        f"Reached maximum entities per spawn ({max_entities}) during herd spawn for {entity_instance.type}")
                    return
                if max_entities_total is not None and existing_entities + total_entities >= max_entities_total:
                    print(
                        f"Reached maximum total entities ({max_entities_total}) during herd spawn for {entity_instance.type}")
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
                    print(f"Generating {entity_instance.type} (Level {effective_level}) at {new_x}, {new_y}")
                    save_map_data(x_pos=new_x, y_pos=new_y, data=data, map_data_dict=mapdb)
                    total_entities += 1
                    herd_spawned += 1
                else:
                    print(f"Failed to spawn herd member at {new_x}, {new_y} for {entity_instance.type}")
            print(f"Herd spawn complete: {herd_spawned}/{herd_size} {entity_instance.type} entities spawned")
        else:
            data = {"type": entity_instance.type}
            data.update(additional_entity_data)
            print(f"Generating single {entity_instance.type} (Level {level}) at {x_pos}, {y_pos}")
            save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)
            total_entities += 1

    print(f"Spawn attempt for {entity_instance.type} complete. Total new entities: {total_entities}")


def generate_additional_entity_data(entity_instance, level):
    attributes = ['type', 'experience', 'armor', 'max_damage', 'role', 'level']
    return {
        attr: getattr(entity_instance, attr, None) * level if attr in ['experience', 'armor', 'max_damage']
        else getattr(entity_instance, attr, None)
        for attr in attributes if hasattr(entity_instance, attr)
    }


def count_entities_of_type(mapdb, entity_type):
    return sum(1 for data in mapdb.values() if "type" in data and data["type"] == entity_type)