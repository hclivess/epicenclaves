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
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(36)
    )


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
                print("user (turn engine)", username, user_data)

                updated_values = {}

                sawmills = 0
                forests = 0

                # Check if the user has "sawmill" and "forest" in the construction section
                for building_data in user_data.get("construction", {}).values():
                    if building_data["type"] == "sawmill":
                        sawmills += 1
                    elif building_data["type"] == "forest":
                        forests += 1

                # Limit wood production by the number of forests, and ensure each sawmill produces at most 1 wood
                if sawmills > 0 and forests > 0:
                    wood_increment = min(sawmills, forests)  # Limited by the smaller of the two
                    updated_values["wood"] = user_data["wood"] + wood_increment

                # Update action_points and age if "action_points" exists
                if "action_points" in user_data:
                    updated_values["action_points"] = user_data["action_points"] + 5
                    updated_values["age"] = user_data["age"] + 1

                food = user_data["food"]

                # Count farms and barracks
                farms = sum(
                    1
                    for entry in get_buildings(user_data)
                    if entry.get("type") == "farm"
                )
                barracks = sum(
                    1
                    for entry in get_buildings(user_data)
                    if entry.get("type") == "barracks"
                )

                # Calculate potential army and peasants addition while respecting the pop_lim
                potential_army_free = min(food, user_data["peasants"], barracks)
                potential_peasants_addition = min(
                    farms,
                    user_data["pop_lim"] - (user_data["peasants"] + potential_army_free),
                )

                updated_values["army_free"] = (
                        user_data.get("army_free", 0) + potential_army_free
                )
                updated_values["peasants"] = (
                        user_data["peasants"] + potential_peasants_addition
                )

                updated_values["food"] = food - 2 * potential_army_free

                # Ensure the sum of army and peasants does not exceed pop_lim
                total_population = (
                        updated_values["peasants"] + updated_values["army_free"] + user_data["army_deployed"]
                )
                while total_population > user_data["pop_lim"]:
                    if potential_army_free > 0:
                        potential_army_free -= 1
                        updated_values["army_free"] -= 1
                        total_population -= 1
                    else:
                        potential_peasants_addition -= 1
                        updated_values["peasants"] -= 1
                        total_population -= 1

                # Ensure free_army doesn't go negative
                if updated_values["army_free"] < 0:
                    updated_values["army_free"] = 0

                # Ensure peasants don't go negative
                if updated_values["peasants"] < 0:
                    updated_values["peasants"] = 0

                # Increase food by one for every leftover peasant
                updated_values["food"] += updated_values["peasants"]

                # Update the user data once, instead of multiple times
                update_user_data(
                    user=username,
                    updated_values=updated_values,
                    user_data_dict=self.usersdb,
                )

                # Print buildings
                print("buildings", get_buildings(user_data))

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

    def stop(self):  # Add this method to stop the thread gracefully
        self.running = False


if __name__ == "__main__":
    turn_engine = TurnEngine()
    turn_engine.start()
    print("Turn engine started")
