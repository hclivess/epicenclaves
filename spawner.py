
import importlib


scenery = importlib.import_module('scenery')
enemies = importlib.import_module('enemies')

from scenery import scenery_types
from enemies import enemy_types

import random
import math
from typing import Dict, Any, List, Tuple
from collections import defaultdict


def calculate_level_for_position(x: int, y: int, map_size: int, min_level: int, max_level: int) -> int:
    distance = math.sqrt(x ** 2 + y ** 2)
    max_distance = math.sqrt(2 * map_size ** 2)
    level_range = max_level - min_level
    level = min_level + int((distance / max_distance) * level_range)
    return min(max(level, min_level), max_level)


def find_nearby_biomes(mapdb: Dict[str, Any], x: int, y: int, radius: int, target_biome: str) -> List[Tuple[int, int]]:
    nearby_biomes = []
    for nx in range(x - radius, x + radius + 1):
        for ny in range(y - radius, y + radius + 1):
            coord_key = f"{nx},{ny}"
            if coord_key in mapdb:
                tile = mapdb[coord_key]
                if isinstance(tile, dict) and tile.get('biome') == target_biome:
                    nearby_biomes.append((nx, ny))
    return nearby_biomes


def spawn_entity(mapdb: Dict[str, Any], entity_class, x: int, y: int, level: int = None) -> bool:
    coord_key = f"{x},{y}"
    if coord_key not in mapdb:
        if level is not None:
            entity = entity_class(level)
        else:
            entity = entity_class()
        mapdb[coord_key] = entity.to_dict()
        return True
    return False


def spawn_herd(mapdb: Dict[str, Any], entity_class, center_x: int, center_y: int, herd_size: int, herd_radius: int,
               base_level: int, min_level: int, max_level: int, is_biome_generation: bool) -> int:
    herd_total = 0
    for _ in range(herd_size):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(1, herd_radius)
        new_x = int(center_x + distance * math.cos(angle))
        new_y = int(center_y + distance * math.sin(angle))
        entity_level = max(min_level, min(max_level, base_level + random.randint(-2, 2)))
        if spawn_entity(mapdb, entity_class, new_x, new_y, None if is_biome_generation else entity_level):
            herd_total += 1

    print(f"Spawned herd of {herd_total} {entity_class.__name__}s at ({center_x}, {center_y})")
    return herd_total


def improved_spawn(mapdb: Dict[str, Any], entity_class, **kwargs):
    params = {
        'min_level': kwargs.get('min_level', getattr(entity_class, 'min_level', 1)),
        'max_level': kwargs.get('max_level', getattr(entity_class, 'max_level', 100)),
        'map_size': kwargs.get('map_size', 1000),
        'max_entities': kwargs.get('max_entities', float('inf')),
        'herd_size': kwargs.get('herd_size', 10),
        'herd_radius': kwargs.get('herd_radius', 5),
        'biome_spawn_chance': kwargs.get('biome_spawn_chance', 0.7),
        'is_biome_generation': kwargs.get('is_biome_generation', False),
        'herd_probability': kwargs.get('herd_probability', 0.5),  # New parameter for herd probability
    }

    biome = getattr(entity_class, 'biome', 'any')
    existing_entities = sum(1 for value in mapdb.values() if value.get('type') == entity_class.type)

    if existing_entities >= params['max_entities']:
        return 0

    total_spawned = 0
    attempts = 0
    max_attempts = params['max_entities'] * 2  # Limit attempts to avoid infinite loops

    while total_spawned < params['max_entities'] and attempts < max_attempts:
        attempts += 1
        x, y = random.randint(1, params['map_size']), random.randint(1, params['map_size'])

        # Calculate the level for this position
        position_level = calculate_level_for_position(x, y, params['map_size'], 1, params['max_level'])

        # Check if the entity's level range is appropriate for this position
        if position_level < params['min_level'] or position_level > params['max_level']:
            continue  # Skip this position if it's not in the entity's level range

        if biome != 'any' and not params['is_biome_generation']:
            nearby_biomes = find_nearby_biomes(mapdb, x, y, 10, biome)  # Changed radius to 10
            herd_spawn_chance = 1.0 if nearby_biomes else params['herd_probability']

            if random.random() < herd_spawn_chance:
                if nearby_biomes:
                    center_x, center_y = random.choice(nearby_biomes)
                else:
                    center_x, center_y = x, y

                base_level = calculate_level_for_position(center_x, center_y, params['map_size'], params['min_level'],
                                                          params['max_level'])
                spawned = spawn_herd(mapdb, entity_class, center_x, center_y, params['herd_size'],
                                     params['herd_radius'],
                                     base_level, params['min_level'], params['max_level'],
                                     params['is_biome_generation'])
                total_spawned += spawned
                continue

        # Single entity spawn for non-biome or if herd spawn didn't occur
        if params['is_biome_generation']:
            if spawn_entity(mapdb, entity_class, x, y):
                total_spawned += 1
        else:
            entity_level = max(params['min_level'], min(params['max_level'], position_level))
            if spawn_entity(mapdb, entity_class, x, y, entity_level):
                total_spawned += 1

    return total_spawned


def spawn_all_entities(mapdb: Dict[str, Any]):
    # Dynamically import scenery and enemies modules
    scenery = importlib.import_module('scenery')
    enemies = importlib.import_module('enemies')

    # Get scenery_types and enemy_types
    scenery_types = getattr(scenery, 'scenery_types', {})
    enemy_types = getattr(enemies, 'enemy_types', {})

    # Spawn scenery
    for entity_class in scenery_types.values():
        improved_spawn(mapdb, entity_class, is_biome_generation=True)

    # Spawn enemies
    for entity_class in enemy_types.values():
        improved_spawn(mapdb, entity_class)

    print(f"Total entities generated: {len(mapdb)}")
    entity_counts = count_entities_of_type(mapdb)
    print("Entity type counts:")
    for entity_type, count in entity_counts.items():
        print(f"  {entity_type}: {count}")


def count_entities_of_type(mapdb: Dict[str, Any]) -> Dict[str, int]:
    counts = defaultdict(int)
    for data in mapdb.values():
        if "type" in data:
            counts[data["type"]] += 1
    return counts


# Example usage
if __name__ == "__main__":
    test_mapdb = {}
    # Assume scenery_types and enemy_types are imported or defined
    spawn_all_entities(test_mapdb, scenery_types, enemy_types)
    print(f"Total entities generated: {len(test_mapdb)}")
    entity_counts = count_entities_of_type(test_mapdb)
    print("Entity type counts:")
    for entity_type, count in entity_counts.items():
        print(f"  {entity_type}: {count}")