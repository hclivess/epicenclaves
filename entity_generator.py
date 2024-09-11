import random
from typing import Dict, Any, List, Tuple
import importlib
import math
from collections import defaultdict

# Import entities module
entities = importlib.import_module('entities')

# Import specific classes from entities
from entities import Enemy, Scenery, entity_types

def find_nearby_biomes(mapdb: Dict[str, Any], x: int, y: int, radius: int, target_biome: str) -> List[Tuple[int, int]]:
    return [(nx, ny) for dx in range(-radius, radius + 1)
            for dy in range(-radius, radius + 1)
            if f"{(nx := x + dx)},{(ny := y + dy)}" in mapdb
            and mapdb[f"{nx},{ny}"].get('biome') == target_biome]

def spawn(mapdb: Dict[str, Any], entity_class, **kwargs):
    probability = kwargs.get('probability', getattr(entity_class, 'probability', 1))
    if probability <= 0:
        return

    min_level = kwargs.get('min_level', getattr(entity_class, 'min_level', 1))
    max_level = kwargs.get('max_level', getattr(entity_class, 'max_level', 2))
    map_size = kwargs.get('map_size', getattr(entity_class, 'map_size', 1000))
    max_entities = kwargs.get('max_entities', getattr(entity_class, 'max_entities', None))
    max_entities_total = kwargs.get('max_entities_total', getattr(entity_class, 'max_entities_total', None))
    herd_size = kwargs.get('herd_size', getattr(entity_class, 'herd_size', 15))
    herd_radius = kwargs.get('herd_radius', getattr(entity_class, 'herd_radius', 5))
    herd_probability = kwargs.get('herd_probability', getattr(entity_class, 'herd_probability', 0.5))
    is_biome_generation = kwargs.get('is_biome_generation', False)

    total_entities = 0
    total_tiles = map_size * map_size
    existing_entities = sum(1 for value in mapdb.values() if value.get('type') == entity_class.type)

    biome = getattr(entity_class, 'biome', 'any')

    if is_biome_generation:
        biome_locations = set((x, y) for x in range(1, map_size + 1) for y in range(1, map_size + 1)
                              if f"{x},{y}" not in mapdb)
    else:
        biome_locations = set((x, y) for x in range(1, map_size + 1) for y in range(1, map_size + 1)
                              if f"{x},{y}" in mapdb and mapdb[f"{x},{y}"].get('biome') == biome)

    if not biome_locations and not is_biome_generation:
        return

    while biome_locations:
        if random.random() > probability or \
           (max_entities is not None and total_entities >= max_entities) or \
           (max_entities_total is not None and existing_entities + total_entities >= max_entities_total) or \
           len(mapdb) >= total_tiles:
            break

        biome_x, biome_y = biome_locations.pop()

        if random.random() <= herd_probability and not is_biome_generation:
            spawn_herd(mapdb, entity_class, biome_x, biome_y, herd_size, map_size, min_level, max_level,
                       max_entities, max_entities_total, existing_entities, total_entities)
        else:
            spawn_single(mapdb, entity_class, biome_x, biome_y, map_size, min_level, max_level, is_biome_generation)
            total_entities += 1

    return total_entities

def spawn_herd(mapdb, entity_class, biome_x, biome_y, herd_size, map_size, min_level, max_level,
               max_entities, max_entities_total, existing_entities, total_entities):
    for _ in range(herd_size):
        if (max_entities is not None and total_entities >= max_entities) or \
           (max_entities_total is not None and existing_entities + total_entities >= max_entities_total):
            return

        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(1, 5)
        new_x = int(biome_x + distance * math.cos(angle))
        new_y = int(biome_y + distance * math.sin(angle))

        if spawn_single(mapdb, entity_class, new_x, new_y, map_size, min_level, max_level):
            total_entities += 1

def spawn_single(mapdb, entity_class, x, y, map_size, min_level, max_level, is_biome_generation=False):
    new_coord_key = f"{x},{y}"
    if 1 <= x <= map_size and 1 <= y <= map_size and new_coord_key not in mapdb:
        entity_level = 1 if is_biome_generation else random.randint(min_level, max_level)
        entity_data = create_entity_data(entity_class, entity_level)
        mapdb[new_coord_key] = entity_data
        return True
    return False

def spawn_all_entities(mapdb):
    for entity_class in entity_types.values():
        if issubclass(entity_class, Scenery) and entity_class != Scenery:
            spawn(mapdb, entity_class, is_biome_generation=True)

    for entity_class in entity_types.values():
        if issubclass(entity_class, Enemy):
            spawn(mapdb, entity_class)

def create_entity_data(entity_class, level):
    return (entity_class(level) if issubclass(entity_class, entities.Enemy) else entity_class()).to_dict()

def count_entities_of_type(mapdb):
    counts = defaultdict(int)
    for data in mapdb.values():
        if "type" in data:
            counts[data["type"]] += 1
    return counts

if __name__ == "__main__":
    test_mapdb = {}
    spawn_all_entities(test_mapdb)
    print(f"Total entities generated: {len(test_mapdb)}")
    entity_counts = count_entities_of_type(test_mapdb)
    print("Entity type counts:")
    for entity_type, count in entity_counts.items():
        print(f"  {entity_type}: {count}")