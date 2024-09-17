import os.path
import random
import threading
import time
from sqlite import save_users_from_memory, save_map_from_memory
from backend import update_user_data, hashify
from player import calculate_population_limit, calculate_total_mana, calculate_total_hp
from map import spawn_entities, count_buildings
from outpost import process_outpost_attacks
from siege import process_siege_attacks
from gnomes import move_gnomes

from scenery import scenery_types
from enemies import enemy_types
from log import log_turn_engine_event

entity_types = {**scenery_types, **enemy_types}

TEST = os.path.exists("test")

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
        start_time = time.time()
        log_turn_engine_event("turn_start", f"Turn {self.turn}")


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

            end_time = time.time()
            execution_time = end_time - start_time
            log_turn_engine_event("turn_end", f"Turn {self.turn}, Execution time: {execution_time:.2f} seconds")
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
            "research": max(0, user_data.get("research", 0) + building_counts.get('laboratory', 0)),
            "action_points": user_data.get("action_points", 0) + 10,
            "age": user_data.get("age", 0) + 1
        }

        # Update ingredients (including resources)
        ingredients = self.calculate_resources(user_data, building_counts)
        updated_values["ingredients"] = ingredients

        current_mana = user_data.get("mana", 0)
        current_hp = user_data.get("hp", 0)
        current_exp = user_data.get("exp", 0)

        max_total_mana = calculate_total_mana(100, current_exp)
        max_total_hp = calculate_total_hp(100, current_exp)

        if current_mana < max_total_mana:
            updated_values["mana"] = min(current_mana + 1, max_total_mana)

        if current_hp < max_total_hp:
            updated_values["hp"] = min(current_hp + 1, max_total_hp)

        updated_values.update(self.calculate_population(user_data, updated_values, building_counts))

        updated_values["score"] = int(current_exp * 10000 / max(1, updated_values["age"]))

        return updated_values

    def calculate_resources(self, user_data, building_counts):
        ingredients = user_data.get("ingredients", {}).copy()

        # Get construction data
        construction = user_data.get("construction", {})

        # Calculate wood production
        sawmills = [b for b in construction.values() if b.get("type") == "sawmill"]
        sawmill_levels = sum(sawmill.get("level", 1) for sawmill in sawmills)
        wood_production = min(sawmill_levels, building_counts.get("forest", 0))
        ingredients["wood"] = ingredients.get("wood", 0) + wood_production

        # Calculate bismuth production
        mines = [b for b in construction.values() if b.get("type") == "mine"]
        mine_levels = sum(mine.get("level", 1) for mine in mines)
        bismuth_production = min(mine_levels, building_counts.get("mountain", 0))
        ingredients["bismuth"] = ingredients.get("bismuth", 0) + bismuth_production

        # Calculate food production
        farms = [b for b in construction.values() if b.get("type") == "farm"]
        food_production = sum(farm.get("level", 1) for farm in farms)
        ingredients["food"] = ingredients.get("food", 0) + food_production

        return ingredients

    def calculate_population(self, user_data, updated_values, building_counts):
        current_population = user_data.get("peasants", 0) + user_data.get("army_free", 0) + user_data.get("army_deployed", 0)
        pop_limit = calculate_population_limit(user_data)

        if current_population > pop_limit:
            excess = current_population - pop_limit
            peasant_reduction = min(excess, user_data.get("peasants", 0))
            army_free = max(0, user_data.get("army_free", 0) - max(0, excess - peasant_reduction))
            return {"peasants": max(0, user_data.get("peasants", 0) - peasant_reduction), "army_free": army_free}

        available_pop_space = pop_limit - current_population
        new_peasants = min(building_counts.get('farm', 0), available_pop_space)
        peasants = user_data.get("peasants", 0) + new_peasants

        max_new_army = min(building_counts.get('barracks', 0), peasants, pop_limit - current_population - new_peasants)
        food_for_army = updated_values["ingredients"]["food"]
        new_army = min(max_new_army, food_for_army // 2)

        updated_values["ingredients"]["food"] -= new_army * 2

        return {
            "peasants": peasants - new_army,
            "army_free": user_data.get("army_free", 0) + new_army
        }