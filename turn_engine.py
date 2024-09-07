import os.path
import random
import blockchain
import threading
import time
from sqlite import save_users_from_memory, save_map_from_memory
from backend import update_user_data, hashify
from entity_generator import spawn_all_entities
from player import calculate_population_limit
import string
import importlib

# Import all entities dynamically
entities = importlib.import_module('entities')

TEST = os.path.exists("test")


def fake_hash():
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(36))


def interruptible_sleep(seconds, interval=1, stop_condition=None):
    total_time_slept = 0
    while total_time_slept < seconds:
        if stop_condition and stop_condition():
            break
        time.sleep(interval)
        total_time_slept += interval


class TurnEngine(threading.Thread):
    def __init__(self, usersdb, mapdb):
        threading.Thread.__init__(self)
        self.latest_block = None
        self.compare_block = None
        self.turn = 0
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
        self.update_latest_block()
        self.turn += 1
        for league in self.mapdb.keys():
            if self.compare_block != self.latest_block:
                self.save_databases(league)
                self.update_users_data(league)
                self.spawn_entities(league)
                print(f"Current turn of {league}: {self.turn}")

    def save_databases(self, league):
        save_map_from_memory(self.mapdb, league=league)
        save_users_from_memory(self.usersdb, league=league)

    def update_latest_block(self):
        self.latest_block = hashify(fake_hash()) if TEST else blockchain.last_bis_hash()

    def update_users_data(self, league):
        for username, user_data in self.usersdb[league].items():
            updated_values = self.calculate_updated_values(user_data)
            update_user_data(user=username, updated_values=updated_values, user_data_dict=self.usersdb[league])

    def calculate_updated_values(self, user_data):
        building_counts = self.count_buildings(user_data)
        updated_values = {}

        updated_values["research"] = self.calculate_research(user_data, building_counts)
        updated_values["ingredients"] = self.calculate_resources(user_data, building_counts)
        updated_values["pop_lim"] = calculate_population_limit(user_data)

        population_data = self.calculate_population(user_data, updated_values, building_counts)
        updated_values.update(population_data)

        updated_values["action_points"] = user_data.get("action_points", 0) + 10
        updated_values["age"] = user_data.get("age", 0) + 1

        return updated_values

    def calculate_research(self, user_data, building_counts):
        return max(0, user_data["research"] + building_counts['laboratory'])

    def calculate_resources(self, user_data, building_counts):
        ingredients = user_data.get("ingredients", {}).copy()

        ingredients["wood"] = max(0, ingredients.get("wood", 0) +
                                  min(building_counts['sawmill'], building_counts['forest']))

        ingredients["bismuth"] = max(0, ingredients.get("bismuth", 0) +
                                     min(building_counts['mine'], building_counts['mountain']))

        ingredients["food"] = max(0, ingredients.get("food", 0) + building_counts['farm'])

        return ingredients

    def calculate_population(self, user_data, updated_values, building_counts):
        population_data = {}

        current_population = (user_data["peasants"] +
                              user_data.get("army_free", 0) +
                              user_data.get("army_deployed", 0))

        pop_limit = updated_values["pop_lim"]

        # Handle case where current population exceeds the limit
        if current_population > pop_limit:
            excess = current_population - pop_limit
            peasant_reduction = min(excess, user_data["peasants"])
            population_data["peasants"] = max(0, user_data["peasants"] - peasant_reduction)
            population_data["army_free"] = user_data.get("army_free", 0)

            # If we still have excess after reducing peasants, reduce army
            if excess > peasant_reduction:
                army_reduction = min(excess - peasant_reduction, population_data["army_free"])
                population_data["army_free"] = max(0, population_data["army_free"] - army_reduction)

            return population_data

        # Calculate available space for new population
        available_pop_space = max(0, pop_limit - current_population)

        # Generate new peasants
        new_peasants = min(building_counts['farm'], available_pop_space)
        population_data["peasants"] = user_data["peasants"] + new_peasants

        # Recalculate available population space
        current_population += new_peasants
        available_pop_space = max(0, pop_limit - current_population)

        # Convert peasants to army units
        max_new_army = min(building_counts['barracks'], population_data["peasants"], available_pop_space)
        food_for_army = updated_values["ingredients"]["food"]
        new_army = min(max_new_army, food_for_army // 2)  # Each army unit costs 2 food

        population_data["army_free"] = user_data.get("army_free", 0) + new_army
        population_data["peasants"] -= new_army
        updated_values["ingredients"]["food"] -= new_army * 2

        return population_data

    def count_buildings(self, user_data):
        counts = {'sawmill': 0, 'forest': 0, 'barracks': 0, 'farm': 0, 'house': 0, 'mine': 0, 'mountain': 0,
                  'laboratory': 0}

        for building_data in user_data.get("construction", {}).values():
            building_type = building_data['type']
            if building_type in counts:
                counts[building_type] += building_data.get('level', 1)

        return counts

    def spawn_entities(self, league):
        spawn_all_entities(self.mapdb[league])