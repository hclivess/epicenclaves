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
    return [
        (nx, ny) for nx in range(x - radius, x + radius + 1)
        for ny in range(y - radius, y + radius + 1)
        if f"{nx},{ny}" in mapdb and mapdb[f"{nx},{ny}"].get('biome') == target_biome
    ]


def calculate_dynamic_probability(base_probability: float, current_count: int, max_count: int) -> float:
    if max_count == 0:
        return base_probability
    scarcity_factor = 1 - (current_count / max_count)
    return min(base_probability + (scarcity_factor * 0.5), 1.0)


def spawn(mapdb: Dict[str, Any], entity_class, **kwargs):
    base_probability = kwargs.get('probability', getattr(entity_class, 'probability', 1))
    if base_probability <= 0:
        return 0

    params = {
        'min_level': kwargs.get('min_level', getattr(entity_class, 'min_level', 1)),
        'max_level': kwargs.get('max_level', getattr(entity_class, 'max_level', 2)),
        'map_size': kwargs.get('map_size', getattr(entity_class, 'map_size', 1000)),
        'max_entities': kwargs.get('max_entities', getattr(entity_class, 'max_entities', float('inf'))),
        'max_entities_total': kwargs.get('max_entities_total',
                                         getattr(entity_class, 'max_entities_total', float('inf'))),
        'herd_size': kwargs.get('herd_size', getattr(entity_class, 'herd_size', 15)),
        'herd_radius': kwargs.get('herd_radius', getattr(entity_class, 'herd_radius', 5)),
        'herd_probability': kwargs.get('herd_probability', getattr(entity_class, 'herd_probability', 0.5)),
        'is_biome_generation': kwargs.get('is_biome_generation', False)
    }

    existing_entities = sum(1 for value in mapdb.values() if value.get('type') == entity_class.type)
    if existing_entities >= params['max_entities_total']:
        return 0

    dynamic_probability = calculate_dynamic_probability(base_probability, existing_entities,
                                                        params['max_entities_total'])

    # Perform probability check first
    if random.random() > dynamic_probability:
        return 0  # Skip if probability check fails

    biome = getattr(entity_class, 'biome', 'any')
    biome_locations = list(get_biome_locations(mapdb, params['map_size'], biome, params['is_biome_generation']))

    if not biome_locations:
        return 0

    total_entities = 0
    while biome_locations and total_entities < params['max_entities'] and existing_entities + total_entities < params[
        'max_entities_total']:
        biome_x, biome_y = random.choice(biome_locations)
        biome_locations.remove((biome_x, biome_y))

        if not params['is_biome_generation'] and random.random() <= params['herd_probability']:
            total_entities += spawn_herd(mapdb, entity_class, biome_x, biome_y, params)
        elif spawn_single(mapdb, entity_class, biome_x, biome_y, params):
            total_entities += 1

    return total_entities


def get_biome_locations(mapdb, map_size, biome, is_biome_generation):
    if is_biome_generation:
        return {(x, y) for x in range(1, map_size + 1) for y in range(1, map_size + 1)
                if f"{x},{y}" not in mapdb}
    else:
        return {(x, y) for x in range(1, map_size + 1) for y in range(1, map_size + 1)
                if f"{x},{y}" in mapdb and mapdb[f"{x},{y}"].get('biome') == biome}


def spawn_herd(mapdb, entity_class, biome_x, biome_y, params):
    herd_total = 0
    for _ in range(params['herd_size']):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(1, params['herd_radius'])
        new_x = int(biome_x + distance * math.cos(angle))
        new_y = int(biome_y + distance * math.sin(angle))

        if spawn_single(mapdb, entity_class, new_x, new_y, params):
            herd_total += 1
    return herd_total


def spawn_single(mapdb, entity_class, x, y, params):
    new_coord_key = f"{x},{y}"
    if 1 <= x <= params['map_size'] and 1 <= y <= params['map_size'] and new_coord_key not in mapdb:
        entity_level = 1 if params['is_biome_generation'] else random.randint(params['min_level'], params['max_level'])
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