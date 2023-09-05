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
        if TEST:
            self.latest_block = hashify(fake_hash())
        else:
            self.latest_block = blockchain.last_bis_hash()

        if self.compare_block != self.latest_block:
            self.save_databases()
            self.turn += 1
            self.compare_block = self.latest_block
            update_turn(self.turn)

            for username, user_data in self.usersdb.items():
                updated_values = {}

                farm_sizes = []

                for building_data in user_data.get("construction", {}).values():
                    if building_data["type"] == "farm":
                        farm_sizes.append(building_data.get("size", 1))

                # Calculate potential peasants addition while respecting the pop_lim
                potential_peasants_addition = min(sum(farm_sizes), user_data["pop_lim"] - user_data["peasants"])

                updated_values["peasants"] = user_data["peasants"] + potential_peasants_addition

                update_user_data(user=username, updated_values=updated_values, user_data_dict=self.usersdb)

            spawn_herd(
                mapdb=self.mapdb,
                entity_class=Boar,
                probability=0.5,
                herd_size=5,
                max_entities=50,
            )

        print(f"Current turn: {self.turn}")

    def run(self):
        while self.running:
            self.check_for_updates()
            if TEST:
                interruptible_sleep(1, stop_condition=lambda: not self.running)
            else:
                interruptible_sleep(30, stop_condition=lambda: not self.running)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    turn_engine = TurnEngine()
    turn_engine.start()
    print("Turn engine started")
