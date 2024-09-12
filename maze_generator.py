import random
import xml.etree.ElementTree as ET


def generate_maze(width, height, offset_x, offset_y):
    # Initialize the maze with walls
    maze = {f'{x},{y}': {'type': 'rock'} for x in range(offset_x, offset_x + width) for y in
            range(offset_y, offset_y + height)}

    def carve_passages(x, y):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if (offset_x <= nx < offset_x + width and offset_y <= ny < offset_y + height
                    and f'{nx},{ny}' in maze):
                maze.pop(f'{x + dx},{y + dy}')
                maze.pop(f'{nx},{ny}')
                carve_passages(nx, ny)

    # Start from a random even coordinate
    start_x = offset_x + random.randrange(0, width, 2)
    start_y = offset_y + random.randrange(0, height, 2)
    maze.pop(f'{start_x},{start_y}')
    carve_passages(start_x, start_y)

    return maze


def generate_multiple_mazes(mapdb, width, height, initial_offset_x, initial_offset_y, spawn_prob, total_max_mazes,
                            map_size):
    print(f"Generating multiple mazes: max {total_max_mazes}, size {width}x{height}, map size {map_size}")
    offset_x = initial_offset_x
    offset_y = initial_offset_y
    total_maze_count = 0

    while total_maze_count < total_max_mazes:
        if offset_x + width > map_size or offset_y + height > map_size:
            print(f"Reached map boundary. Stopping maze generation.")
            break

        if random.random() <= spawn_prob:
            print(f"\nGenerating maze {total_maze_count + 1} at offset ({offset_x}, {offset_y})")
            maze = generate_maze(width, height, offset_x, offset_y)
            mapdb.update(maze)
            total_maze_count += 1
            print(f"Maze {total_maze_count} added to map")

        offset_x += width + initial_offset_x
        if offset_x + width > map_size:
            offset_x = initial_offset_x
            offset_y += height + initial_offset_y
            print(f"Moving to next row. New offset: ({offset_x}, {offset_y})")

    print(f"Generation complete. Total mazes generated: {total_maze_count}")

def create_svg(mapdb, map_size, cell_size=5):
    svg_size = map_size * cell_size
    svg = ET.Element('svg', width=str(svg_size), height=str(svg_size),
                     viewBox=f"0 0 {svg_size} {svg_size}",
                     xmlns="http://www.w3.org/2000/svg")

    # Background (implicitly empty)
    ET.SubElement(svg, 'rect', width="100%", height="100%", fill="#f0f0f0")

    # Rocks
    for coord, cell in mapdb.items():
        if cell['type'] == 'rock':
            x, y = map(int, coord.split(','))
            ET.SubElement(svg, 'rect',
                          x=str(x * cell_size),
                          y=str(y * cell_size),
                          width=str(cell_size),
                          height=str(cell_size),
                          fill="#404040")

    return ET.tostring(svg, encoding='unicode')


if __name__ == "__main__":
    mapdb = {}
    map_size = 1000
    maze_width = 51 # Odd number to ensure walls on all sides
    maze_height = 51  # Odd number to ensure walls on all sides
    initial_offset = 5
    spawn_probability = 0.5
    max_mazes = 20

    generate_multiple_mazes(mapdb, maze_width, maze_height, initial_offset, initial_offset,
                            spawn_probability, max_mazes, map_size)

    svg_output = create_svg(mapdb, map_size)

    # Save SVG to a file
    with open('maze.svg', 'w') as f:
        f.write(svg_output)

    print("SVG maze image has been saved as 'maze.svg'")