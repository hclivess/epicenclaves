import json


def load_leagues():
    try:
        with open("config_enclaves.json") as input_file:
            config_data = json.load(input_file)

        leagues = config_data.get("leagues", {})

        # Return a list of league names
        return list(leagues.keys())
    except FileNotFoundError:
        print("Error: config_enclaves.json file not found.")
        return []
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config_enclaves.json file.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return []


# Example usage
if __name__ == "__main__":
    leagues = load_leagues()
    print("Available leagues:", leagues)