import sqlite3
import sys

def wipe_league(league):
    # Connect to the databases
    map_conn = sqlite3.connect("db/map_data.db")
    user_conn = sqlite3.connect("db/user_data.db")

    try:
        # Wipe map data for the specific league
        map_cursor = map_conn.cursor()
        map_cursor.execute(f"DELETE FROM {league}")
        map_conn.commit()
        print(f"Wiped map data for league: {league}")

        # Wipe user data for the specific league
        user_cursor = user_conn.cursor()
        user_cursor.execute(f"DELETE FROM {league}_user_data")
        user_conn.commit()
        print(f"Wiped user data for league: {league}")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connections
        map_conn.close()
        user_conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python wipe_league.py <league_name>")
        sys.exit(1)

    league_to_wipe = sys.argv[1]
    wipe_league(league_to_wipe)
    print(f"Finished wiping data for league: {league_to_wipe}")