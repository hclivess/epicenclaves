import json
import sqlite3

def create_map_table():
    # Connect to the database or create one if it doesn't exist
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Create a table for the map data with columns: x_pos, y_pos, data
    cursor.execute('''CREATE TABLE IF NOT EXISTS map_data (
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT,
                        PRIMARY KEY (x_pos, y_pos)
                      )''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def save_map_data(x_pos, y_pos, data):
    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Convert the data dictionary to a string for storage
    data_str = json.dumps(data)

    # Insert or replace data for the given position
    cursor.execute("INSERT OR REPLACE INTO map_data (x_pos, y_pos, data) VALUES (?, ?, ?)",
                   (x_pos, y_pos, data_str))

    # Commit changes and close the connection
    conn.commit()
    conn.close()




def get_map_data(x_pos, y_pos):
    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Retrieve data and control for the given position
    cursor.execute("SELECT x_pos, y_pos, data FROM map_data WHERE x_pos = ? AND y_pos = ?", (x_pos, y_pos))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    if result:
        x_pos, y_pos, data_str = result
        # Convert the data string back to a dictionary
        data = json.loads(data_str)
        return {"x_pos": x_pos, "y_pos": y_pos, **data}  # Unpacks the data dictionary

    # Return None if no entity was found
    return None



