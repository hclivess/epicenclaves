import random

def generate_maze(width, height, offset_x, offset_y):
    maze = {}
    for y in range(offset_y, offset_y + height, 2):
        for x in range(offset_x, offset_x + width, 2):
            key = f'{x},{y}'
            maze[key] = {'type': 'wall'}

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
    return maze

def generate_multiple_mazes(mapdb, width, height, initial_offset_x, initial_offset_y, spawn_prob, total_max_mazes, size):
    print("generating maze")
    offset_x = initial_offset_x
    offset_y = initial_offset_y
    total_maze_count = 0

    while total_maze_count < total_max_mazes:
        if offset_x + width > size or offset_y + height > size:
            break

        if random.random() <= spawn_prob:
            maze = generate_maze(width, height, offset_x, offset_y)
            mapdb.update(maze)

        offset_x += width + initial_offset_x
        if offset_x + width > size:
            offset_x = initial_offset_x
            offset_y += height + initial_offset_y

        total_maze_count += 1


if __name__ == "__main__":
    # Initialize an empty map database
    mapdb = {}

    # Generate mazes with a 50% probability each within a 100x100 area
    generate_multiple_mazes(mapdb, 10, 10, 5, 5, 0.5, 20, 100)

    # Print the map database to see what was generated
print(mapdb)
