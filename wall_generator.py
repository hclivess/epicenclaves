import random

def generate_maze(width, height, offset_x, offset_y, spawn_prob, spawn_every_x_tiles, spawn_every_y_tiles, entity_count):
    maze = {}
    local_entity_count = 0

    for y in range(offset_y, offset_y + height, 2):
        for x in range(offset_x, offset_x + width, 2):
            key = f'{x},{y}'
            maze[key] = {'type': 'wall'}

            if x % spawn_every_x_tiles == 0 and y % spawn_every_y_tiles == 0 and random.random() < spawn_prob:
                maze[key] = {'type': 'spawn', 'entity_id': entity_count}
                entity_count += 1
                local_entity_count += 1

            neighbor_x = x + 1 if x < offset_x + width - 2 else None
            neighbor_y = y - 1 if y > offset_y + 1 else None

            if neighbor_x and neighbor_y:
                if random.choice([True, False]):
                    maze[f'{x},{neighbor_y}'] = {'type': 'wall'}
                else:
                    maze[f'{neighbor_x},{y}'] = {'type': 'wall'}
            elif neighbor_y:
                maze[f'{x},{neighbor_y}'] = {'type': 'wall'}
            elif neighbor_x:
                maze[f'{neighbor_x},{y}'] = {'type': 'wall'}

    return maze, local_entity_count, entity_count

def generate_multiple_mazes(mapdb, width, height, initial_offset_x, initial_offset_y, spawn_prob, spawn_every_x_tiles, spawn_every_y_tiles, total_max_mazes):
    offset_x = initial_offset_x
    offset_y = initial_offset_y
    total_entity_count = 0
    total_maze_count = 0

    while total_maze_count < total_max_mazes:
        maze, local_entity_count, total_entity_count = generate_maze(width, height, offset_x, offset_y, spawn_prob, spawn_every_x_tiles, spawn_every_y_tiles, total_entity_count)
        mapdb.update(maze)

        total_maze_count += 1
        offset_x += width + 2
        offset_y += height + 2

mapdb = {}
generate_multiple_mazes(mapdb, 10, 10, 50, 50, 0.5, 100, 100, 3)
