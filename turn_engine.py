import os.path
import random
import blockchain
import threading
import time
from sqlite import save_users_from_memory, save_map_from_memory
from backend import update_user_data, hashify
from player import calculate_population_limit
import string
import importlib
from map import spawn_entities, count_buildings
from outpost import process_outpost_attacks
from siege import process_siege_attacks
from gnomes import move_gnomes

# Import all entities dynamically
entities = importlib.import_module('entities')

TEST = os.path.exists("test")


def fake_hash():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=36))


def interruptible_sleep(seconds, interval=1, stop_condition=None):
    end_time = time.time() + seconds
    while time.time() < end_time:
        if stop_condition and stop_condition():
            break
        time.sleep(min(interval, end_time - time.time()))


class TurnEngine(threading.Thread):
    def __init__(self, usersdb, mapdb):
        super().__init__()
        self.turn = 0
        self.round_time = 0
        self.running = True
        self.usersdb = usersdb
        self.mapdb = mapdb

    def run(self):
        while self.running:
            self.process_turn()
            sleep_time = 1 if TEST else 30
            print("Cycle closed")
            interruptible_sleep(sleep_time, stop_condition=lambda: not self.running)

    def stop(self):
        self.running = False

    def process_turn(self):
        if time.time() - self.round_time > 60:
            start_time = time.time()  # Start the timer

            self.round_time = time.time()
            self.turn += 1

            for league in self.mapdb:
                    self.save_databases(league)
                    self.update_users_data(league)
                    spawn_entities(self.mapdb, league)
                    print("Processing sieges")
                    process_siege_attacks(self.mapdb, self.usersdb, league)
                    print("Processing outposts")
                    process_outpost_attacks(self.mapdb, self.usersdb, league)
                    print("Moving gnomes")
                    move_gnomes(self.mapdb, league)
                    print(f"Current turn of {league}: {self.turn}")

            end_time = time.time()  # End the timer
            execution_time = end_time - start_time  # Calculate the execution time
            print(f"Turn {self.turn} execution time: {execution_time:.2f} seconds")


    def save_databases(self, league):
        save_map_from_memory(self.mapdb, league=league)
        save_users_from_memory(self.usersdb, league=league)

    def update_users_data(self, league):
        league_users = self.usersdb[league]
        for username, user_data in league_users.items():
            updated_values = self.calculate_updated_values(user_data)
            update_user_data(user=username, updated_values=updated_values, user_data_dict=league_users)

    def calculate_updated_values(self, user_data):
        building_counts = count_buildings(user_data)

        updated_values = {
            "research": max(0, user_data["research"] + building_counts['laboratory']),
            "ingredients": self.calculate_resources(user_data, building_counts),
            "pop_lim": calculate_population_limit(user_data),
            "action_points": user_data.get("action_points", 0) + 10,
            "age": user_data.get("age", 0) + 1
        }

        updated_values.update(self.calculate_population(user_data, updated_values, building_counts))

        updated_values["score"] = int(user_data.get("exp", 0) * 10000 / max(1, updated_values["age"]))

        return updated_values

    def calculate_resources(self, user_data, building_counts):
        ingredients = user_data.get("ingredients", {}).copy()

        # Calculate wood production
        sawmill_levels = sum(sawmill.get("level", 1) for sawmill in user_data.get("sawmills", []))
        wood_production = min(sawmill_levels, building_counts["forest"])
        ingredients["wood"] = max(0, ingredients.get("wood", 0) + wood_production)

        # Calculate bismuth production
        mine_levels = sum(mine.get("level", 1) for mine in user_data.get("mines", []))
        bismuth_production = min(mine_levels, building_counts["mountain"])
        ingredients["bismuth"] = max(0, ingredients.get("bismuth", 0) + bismuth_production)

        # Calculate food production (unchanged)
        ingredients["food"] = max(0, ingredients.get("food", 0) + building_counts['farm'])

        return ingredients

    def calculate_population(self, user_data, updated_values, building_counts):
        current_population = user_data["peasants"] + user_data.get("army_free", 0) + user_data.get("army_deployed", 0)
        pop_limit = updated_values["pop_lim"]

        if current_population > pop_limit:
            excess = current_population - pop_limit
            peasant_reduction = min(excess, user_data["peasants"])
            army_free = max(0, user_data.get("army_free", 0) - max(0, excess - peasant_reduction))
            return {"peasants": max(0, user_data["peasants"] - peasant_reduction), "army_free": army_free}

        available_pop_space = pop_limit - current_population
        new_peasants = min(building_counts['farm'], available_pop_space)
        peasants = user_data["peasants"] + new_peasants

        max_new_army = min(building_counts['barracks'], peasants, pop_limit - current_population - new_peasants)
        food_for_army = updated_values["ingredients"]["food"]
        new_army = min(max_new_army, food_for_army // 2)

        updated_values["ingredients"]["food"] -= new_army * 2

        return {
            "peasants": peasants - new_army,
            "army_free": user_data.get("army_free", 0) + new_army
        }