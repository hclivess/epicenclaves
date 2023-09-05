import random
import blockchain
import threading
import time
from sqlite import update_turn
from user import save_users_from_memory
from backend import update_user_data, hashify
from map import get_buildings, save_map_from_memory
from entities import Boar
from entity_generator import spawn_herd
import string

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
            update_user_data(user=username, updated_values=updated_values, user_data_dict=self.usersdb)

    def calculate_updated_values(self, user_data):
        building_counts = self.count_buildings(user_data)
        updated_values = {}

        wood_increment = min(building_counts['sawmills'], building_counts['forests'])
        updated_values["wood"] = user_data["wood"] + wood_increment

        potential_army_free = min(user_data["food"] // 2, user_data["peasants"], building_counts['barracks'])
        updated_values["army_free"] = user_data.get("army_free", 0) + potential_army_free
        updated_values["food"] = user_data["food"] - 2 * potential_army_free

        potential_peasants_addition = min(
            building_counts['farms'], user_data["pop_lim"] - (user_data["peasants"] + potential_army_free))
        updated_values["peasants"] = user_data["peasants"] + potential_peasants_addition

        return updated_values

    def count_buildings(self, user_data):
        counts = {'sawmills': 0, 'forests': 0, 'barracks': 0, 'farms': 0}
        for building_data in user_data.get("construction", {}).values():
            counts[building_data['type']] += building_data.get('size', 1)

        return counts

    def spawn_entities(self):
        spawn_herd(
            mapdb=self.mapdb,
            entity_class=Boar,
            probability=0.5,
            herd_size=5,
            max_entities=50,
        )

    def run(self):
        while self.running:
            self.check_for_updates()
            sleep_time = 1 if TEST else 30
            interruptible_sleep(sleep_time, stop_condition=lambda: not self.running)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    turn_engine = TurnEngine({}, {})
    turn_engine.start()
    print("Turn engine started")
