import json
import sqlite3

def create_map_table():
    # Connect to the database or create one if it doesn't exist
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Create a table for the map data with columns: x_pos, y_pos, data, control
    cursor.execute('''CREATE TABLE IF NOT EXISTS map_data (
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT,
                        control TEXT,
                        PRIMARY KEY (x_pos, y_pos)
                      )''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def save_map_data(x_pos, y_pos, data, control):
    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Convert the data dictionary to a string for storage
    data_str = json.dumps(data)

    # Insert or replace data for the given position
    cursor.execute("INSERT OR REPLACE INTO map_data (x_pos, y_pos, data, control) VALUES (?, ?, ?, ?)",
                   (x_pos, y_pos, data_str, control))

    # Commit changes and close the connection
    conn.commit()
    conn.close()




def get_map_data(x_pos, y_pos):
    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Retrieve data and control for the given position
    cursor.execute("SELECT x_pos, y_pos, data, control FROM map_data WHERE x_pos = ? AND y_pos = ?", (x_pos, y_pos))
    results = cursor.fetchall()

    # Close the connection
    conn.close()

    entities = []
    for result in results:
        x_pos, y_pos, data_str, control = result
        # Convert the data string back to a dictionary
        data = json.loads(data_str)
        entities.append({"x_pos": x_pos, "y_pos": y_pos, "data": data, "control": control})

    return entities


