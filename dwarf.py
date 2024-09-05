import random
from PIL import Image, ImageDraw
import time
import json
import sqlite3


def diamond_square(size, roughness):
    def diamond_step(x, y, step, rand_range):
        count = 0
        total = 0
        for dx, dy in [(-step, -step), (-step, step), (step, -step), (step, step)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < size and 0 <= ny < size:
                total += grid[nx][ny]
                count += 1
        avg = total / count if count > 0 else 0
        grid[x][y] = avg + random.uniform(-rand_range, rand_range)

    def square_step(x, y, step, rand_range):
        count = 0
        total = 0
        for dx, dy in [(-step, 0), (step, 0), (0, -step), (0, step)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < size and 0 <= ny < size:
                total += grid[nx][ny]
                count += 1
        avg = total / count if count > 0 else 0
        grid[x][y] = avg + random.uniform(-rand_range, rand_range)

    grid = [[random.uniform(0, 1) for _ in range(size)] for _ in range(size)]

    step = size - 1
    rand_range = 1.0

    while step > 1:
        half_step = step // 2

        for x in range(half_step, size, step):
            for y in range(half_step, size, step):
                diamond_step(x, y, half_step, rand_range)

        for x in range(0, size, step):
            for y in range(half_step, size, step):
                square_step(x, y, half_step, rand_range)
        for x in range(half_step, size, step):
            for y in range(0, size, step):
                square_step(x, y, half_step, rand_range)

        step = half_step
        rand_range *= roughness

    return [[max(0, min(1, cell)) for cell in row] for row in grid]


def generate_moisture_map(size):
    base = diamond_square(size, 0.5)
    return [[cell ** 0.5 for cell in row] for row in base]


def get_biome_type(elevation, moisture, is_water=False):
    if is_water:
        return "water"
    if elevation > 0.8:
        return "mountain"
    elif elevation > 0.6:
        return "forest" if moisture > 0.6 else "grassland"
    elif elevation > 0.3:
        if moisture > 0.7:
            return "swamp"
        elif moisture > 0.4:
            return "forest"
        else:
            return "grassland"
    else:
        if moisture > 0.6:
            return "grassland"
        else:
            return "desert"


def get_biome_color(biome_type):
    color_map = {
        "water": (65, 105, 225),
        "mountain": (128, 128, 128),
        "forest": (0, 100, 0),
        "grassland": (34, 139, 34),
        "swamp": (0, 128, 128),
        "desert": (210, 180, 140)
    }
    return color_map.get(biome_type, (0, 0, 0))


def generate_rivers(elevation_map, water_map, count):
    size = len(elevation_map)
    for _ in range(count):
        x, y = random.randint(0, size - 1), random.randint(0, size - 1)
        while elevation_map[y][x] < 0.7:  # Start from high elevation
            x, y = random.randint(0, size - 1), random.randint(0, size - 1)

        for _ in range(size // 2):  # Limit river length
            water_map[y][x] = True

            lowest = min([(nx, ny) for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
                          if 0 <= nx < size and 0 <= ny < size],
                         key=lambda coord: elevation_map[coord[1]][coord[0]])

            x, y = lowest
            if elevation_map[y][x] < 0.3 or water_map[y][x]:  # River reaches low elevation or existing water
                break


def generate_dwarf_fortress_style_map(map_size=256):
    print("Generating elevation map...")
    elevation_map = diamond_square(map_size, 0.5)
    print("Generating moisture map...")
    moisture_map = generate_moisture_map(map_size)

    print("Creating water features...")
    water_map = [[False for _ in range(map_size)] for _ in range(map_size)]
    generate_rivers(elevation_map, water_map, map_size // 100)

    print("Creating biome map...")
    biome_map = []
    terrain_data = {}

    for y in range(map_size):
        row = []
        for x in range(map_size):
            elevation = elevation_map[y][x]
            moisture = moisture_map[y][x]
            is_water = water_map[y][x]
            biome_type = get_biome_type(elevation, moisture, is_water)
            biome_color = get_biome_color(biome_type)
            row.append(biome_color)

            terrain_data[f"{x + 1},{y + 1}"] = {"type": biome_type}

        biome_map.append(row)

    return biome_map, terrain_data


def create_image_from_map(biome_map, pixel_size=2):
    map_size = len(biome_map)
    image_size = map_size * pixel_size
    image = Image.new('RGB', (image_size, image_size))
    draw = ImageDraw.Draw(image)

    for y in range(map_size):
        for x in range(map_size):
            color = biome_map[y][x]
            draw.rectangle([x * pixel_size, y * pixel_size, (x + 1) * pixel_size, (y + 1) * pixel_size], fill=color)

    return image


def create_sqlite_database(terrain_data):
    conn = sqlite3.connect('map_data.db')
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game
    (x_pos INTEGER, y_pos INTEGER, data TEXT)
    ''')

    # Insert data
    for coord, data in terrain_data.items():
        x, y = map(int, coord.split(','))
        cursor.execute('INSERT INTO game (x_pos, y_pos, data) VALUES (?, ?, ?)',
                       (x, y, json.dumps(data)))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Generating Dwarf Fortress-style map...")
    start_time = time.time()

    map_size = 256  # Use a power of 2 for best results
    biome_map, terrain_data = generate_dwarf_fortress_style_map(map_size)

    print("Map generation complete.")
    print("Creating image...")

    image = create_image_from_map(biome_map)
    image.save("df_style_terrain_map.png")

    print("Saving terrain data to JSON...")
    with open("terrain_data.json", "w") as f:
        json.dump(terrain_data, f, indent=2)

    print("Saving terrain data to SQLite database...")
    create_sqlite_database(terrain_data)

    end_time = time.time()
    print(f"Map generated and saved as 'df_style_terrain_map.png'")
    print(f"Terrain data saved as 'terrain_data.json' and in 'map_data.db'")
    print(f"Total time: {end_time - start_time:.2f} seconds")