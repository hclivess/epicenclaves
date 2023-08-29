from PIL import Image, ImageDraw
import random

def generate_maze(width, height):
    maze = [['wall' for _ in range(width)] for _ in range(height)]

    # Generate maze using binary tree algorithm
    for y in range(1, height, 2):
        for x in range(1, width, 2):
            maze[y][x] = 'path'

            if y > 1 and x < width - 2:
                if random.choice([True, False]):
                    maze[y - 1][x] = 'path'
                else:
                    maze[y][x + 1] = 'path'
            elif y > 1:
                maze[y - 1][x] = 'path'
            elif x < width - 2:
                maze[y][x + 1] = 'path'

    return maze

def maze_to_image(maze, offset_x, offset_y):
    cell_size = 10  # Size of each maze cell in pixels

    width = len(maze[0])
    height = len(maze)

    image_width = width * cell_size
    image_height = height * cell_size

    # Adjust image dimensions to account for offset
    image_width += offset_x
    image_height += offset_y

    image = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(image)

    for y in range(height):
        for x in range(width - 1):
            if maze[y][x] == 'path' and maze[y][x + 1] == 'path':
                draw_line(draw, x, y, x + 1, y, cell_size, offset_x, offset_y)

    for x in range(width):
        for y in range(height - 1):
            if maze[y][x] == 'path' and maze[y + 1][x] == 'path':
                draw_line(draw, x, y, x, y + 1, cell_size, offset_x, offset_y)

    return image

def draw_line(draw, x1, y1, x2, y2, cell_size, offset_x, offset_y):
    x1 = x1 * cell_size + offset_x
    y1 = y1 * cell_size + offset_y
    x2 = x2 * cell_size + offset_x
    y2 = y2 * cell_size + offset_y
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        draw.point((x1, y1), fill='black')
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

def update_mapdb_with_maze(mapdb, maze, offset_x, offset_y):
    for y, row in enumerate(maze):
        for x, cell_type in enumerate(row):
            if cell_type == 'wall':
                mapdb[f'{x + offset_x},{y + offset_y}'] = {'type': 'wall'}

# Example usage
if __name__ == "__main__":
    mapdb = {}
    maze = generate_maze(20, 20)  # Adjust width and height as needed
    offset_x = 50  # Adjust the offset values as needed
    offset_y = 50
    update_mapdb_with_maze(mapdb, maze, offset_x, offset_y)
    print(mapdb)

    maze_image = maze_to_image(maze, offset_x, offset_y)
    maze_image.save('maze_with_offset.png')
