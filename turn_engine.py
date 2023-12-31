import os.path
import random
import blockchain
import threading
import time
from sqlite import update_turn
from user import save_users_from_memory
from backend import update_user_data, hashify
from map import save_map_from_memory
from entities import Boar, Wolf, Valenthis
from entity_generator import spawn
import string

if os.path.exists("test"):
    TEST = 1
else:
    TEST = 0

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

    def save_databases(self):
        save_map_from_memory(self.mapdb)
        save_users_from_memory(self.usersdb)

    def check_for_updates(self):
        self.update_latest_block()
        if self.compare_block != self.latest_block:
            self.save_databases()
            self.update_turn()
            self.update_users_data()
            self.spawn_entities()
            print(f"Current turn: {self.turn}")

    def update_latest_block(self):
        self.latest_block = hashify(fake_hash()) if TEST else blockchain.last_bis_hash()

    def update_turn(self):
        self.turn += 1
        self.compare_block = self.latest_block
        update_turn(self.turn)

    def update_users_data(self):
        for username, user_data in self.usersdb.items():
            updated_values = self.calculate_updated_values(user_data)

            # Update action_points and age if "action_points" exists
            if "action_points" in user_data:
                updated_values["action_points"] = user_data["action_points"] + 5
                updated_values["age"] = user_data["age"] + 1

            update_user_data(user=username, updated_values=updated_values, user_data_dict=self.usersdb)

    def calculate_updated_values(self, user_data):
        building_counts = self.count_buildings(user_data)
        updated_values = {}

        research_increment = building_counts['laboratory']
        updated_values["research"] = max(0, user_data["research"] + research_increment)

        wood_increment = min(building_counts['sawmill'], building_counts['forest'])
        updated_values["wood"] = max(0, user_data["wood"] + wood_increment)

        bis_increment = min(building_counts['mine'], building_counts['mountain'])
        updated_values["bismuth"] = max(0, user_data["bismuth"] + bis_increment)

        current_population = user_data["peasants"] + user_data.get("army_free", 0) + user_data.get("army_deployed", 0)
        available_pop_space = max(0, user_data["pop_lim"] - current_population)

        # Calculate the potential new army
        potential_army_free = min(user_data["food"] // 2, user_data["peasants"], building_counts['barracks'],
                                  available_pop_space)
        updated_values["army_free"] = max(0, user_data.get("army_free", 0) + potential_army_free)
        updated_values["food"] = max(0, user_data["food"] - 2 * potential_army_free)

        # Update available population space after army calculations
        current_population = user_data["peasants"] + updated_values["army_free"] + user_data.get("army_deployed", 0)
        available_pop_space = max(0, user_data["pop_lim"] - current_population)

        potential_peasants_addition = min(building_counts['farm'], available_pop_space)
        updated_values["peasants"] = max(0, user_data["peasants"] + potential_peasants_addition)

        return updated_values

    def count_buildings(self, user_data):
        counts = {'sawmill': 0, 'forest': 0, 'barracks': 0, 'farm': 0, 'house': 0, 'mine': 0, 'mountain': 0, 'laboratory': 0}

        for building_data in user_data.get("construction", {}).values():
            building_type = building_data['type']
            if building_type not in counts:
                counts[building_type] = 0
            counts[building_type] += building_data.get('level', 1)

        return counts

    def spawn_entities(self):
        random_level = random.randint(1, 10)
        spawn(
            mapdb=self.mapdb,
            entity_instance=Boar(),
            probability=0.05,
            herd_size=5,
            max_entities=50,
            level=random_level,
            herd_probability=1

        )

        random_level = random.randint(1, 20)
        spawn(
            mapdb=self.mapdb,
            entity_instance=Wolf(),
            probability=0.05,
            herd_size=7,
            max_entities=50,
            level=random_level,
            herd_probability=1

        )

        spawn(
            mapdb=self.mapdb,
            entity_instance=Valenthis(),
            probability=0.001,
            size=200,
            max_entities=1,
            level=1,
            herd_probability=1
        )

    def run(self):
        while self.running:
            self.check_for_updates()
            sleep_time = 1 if TEST else 30
            print("Cycle closed")
            interruptible_sleep(sleep_time, stop_condition=lambda: not self.running)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    turn_engine = TurnEngine({}, {})
    turn_engine.start()
    print("Turn engine started")
