import random
import importlib
import math

# Import all entities from a separate module
entities = importlib.import_module('entities')


def generate_random_level(base_level):
    """Generates a random level between `base_level` and 100, with exponentially decreasing probability."""
    max_level = 100
    # Decay factor: higher values make high levels rarer
    decay = 0.05

    while True:
        level = base_level
        while level < max_level:
            if random.random() > math.exp(-decay * (level - base_level)):
                return level
            level += 1
        if level == max_level:
            return level


def spawn_all_entities(mapdb):
    entity_classes = [cls for name, cls in entities.__dict__.items() if isinstance(cls, type) and hasattr(cls, 'type')]
    for entity_class in entity_classes:
        entity_instance = entity_class()
        spawn(
            entity_class=entity_class,
            probability=getattr(entity_instance, 'probability', 1),
            mapdb=mapdb,
            level=generate_random_level(getattr(entity_instance, 'level', 1)),
            map_size=getattr(entity_instance, 'map_size', 101),
            max_entities=getattr(entity_instance, 'max_entities', None),
            max_entities_total=getattr(entity_instance, 'max_entities_total', None),
            herd_probability=getattr(entity_instance, 'herd_probability', 0.5)
        )


def spawn(entity_class, probability, mapdb, level, map_size=101, max_entities=None, max_entities_total=None,
          herd_size=15, herd_radius=5, herd_probability=0.5):
    total_entities = 0
    total_tiles = map_size * map_size
    existing_entities = sum(1 for value in mapdb.values() if value.get('type') == entity_class.type)

    print(f"Attempting to spawn {entity_class.type} entities:")
    print(f"  - Probability: {probability}")
    print(f"  - Max entities per spawn: {max_entities if max_entities is not None else 'Unlimited'}")
    print(f"  - Max total entities: {max_entities_total if max_entities_total is not None else 'Unlimited'}")
    print(f"  - Current entities on map: {existing_entities}")
    print(f"  - Map size: {map_size}x{map_size}")

    while True:
        if random.random() > probability:
            print(f"Spawn attempt for {entity_class.type} skipped due to low probability ({probability})")
            break

        if max_entities is not None and total_entities >= max_entities:
            print(f"Reached maximum entities per spawn ({max_entities}) for {entity_class.type}")
            return

        if max_entities_total is not None and existing_entities + total_entities >= max_entities_total:
            print(f"Reached maximum total entities ({max_entities_total}) for {entity_class.type}")
            return

        if len(mapdb) >= total_tiles:
            print(f"No more empty tiles available ({len(mapdb)}/{total_tiles}) for {entity_class.type}")
            return

        x_pos = random.randint(1, map_size)
        y_pos = random.randint(1, map_size)
        coord_key = f"{x_pos},{y_pos}"

        if coord_key in mapdb:
            print(f"Tile {coord_key} is occupied, trying another location for {entity_class.type}")
            continue

        if random.random() <= herd_probability:
            print(f"Attempting to spawn a herd of {entity_class.type}")
            level_one_count = max(1, int(0.1 * herd_size))
            herd_spawned = 0
            for idx in range(herd_size):
                if max_entities is not None and total_entities >= max_entities:
                    print(
                        f"Reached maximum entities per spawn ({max_entities}) during herd spawn for {entity_class.type}")
                    return
                if max_entities_total is not None and existing_entities + total_entities >= max_entities_total:
                    print(
                        f"Reached maximum total entities ({max_entities_total}) during herd spawn for {entity_class.type}")
                    return
                effective_level = 1 if idx < level_one_count else generate_random_level(level)
                x_offset = random.randint(-herd_radius, herd_radius)
                y_offset = random.randint(-herd_radius, herd_radius)
                new_x = x_pos + x_offset
                new_y = y_pos + y_offset
                new_coord_key = f"{new_x},{new_y}"

                if 1 <= new_x <= map_size and 1 <= new_y <= map_size and new_coord_key not in mapdb:
                    entity_data = create_entity_data(entity_class, effective_level)
                    print(f"Generating {entity_class.type} (Level {effective_level}) at {new_x}, {new_y}")
                    save_map_data(x_pos=new_x, y_pos=new_y, data=entity_data, map_data_dict=mapdb)
                    total_entities += 1
                    herd_spawned += 1
                else:
                    print(f"Failed to spawn herd member at {new_x}, {new_y} for {entity_class.type}")
            print(f"Herd spawn complete: {herd_spawned}/{herd_size} {entity_class.type} entities spawned")
        else:
            entity_data = create_entity_data(entity_class, level)
            print(f"Generating single {entity_class.type} (Level {level}) at {x_pos}, {y_pos}")
            save_map_data(x_pos=x_pos, y_pos=y_pos, data=entity_data, map_data_dict=mapdb)
            total_entities += 1

    print(f"Spawn attempt for {entity_class.type} complete. Total new entities: {total_entities}")


def create_entity_data(entity_class, level):
    if issubclass(entity_class, entities.Enemy):
        entity_instance = entity_class(level=level)
        return {
            "type": entity_class.type,
            "level": level,
            "hp": entity_instance.hp,
            "max_hp": entity_instance.hp,
            "armor": entity_instance.armor,
            "max_damage": entity_instance.max_damage,
            "role": entity_instance.role,
        }
    else:
        entity_instance = entity_class()
        return {
            "type": entity_class.type,
            "role": getattr(entity_instance, 'role', 'scenery'),
            "hp": getattr(entity_instance, 'hp', None),
        }


def save_map_data(map_data_dict, x_pos, y_pos, data):
    # Use a string coordinate key like 'x,y'
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data


def count_entities_of_type(mapdb, entity_type):
    return sum(1 for data in mapdb.values() if "type" in data and data["type"] == entity_type)


if __name__ == "__main__":
    # Test the entity generation
    test_mapdb = {}
    spawn_all_entities(test_mapdb)
    print("Entity generation test complete.")
    print(f"Total entities generated: {len(test_mapdb)}")
    entity_counts = {}
    for entity in test_mapdb.values():
        entity_type = entity['type']
        if entity_type not in entity_counts:
            entity_counts[entity_type] = 0
        entity_counts[entity_type] += 1

    print("Entity type counts:")
    for entity_type, count in entity_counts.items():
        print(f"  {entity_type}: {count}")
