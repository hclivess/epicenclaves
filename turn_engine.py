import asyncio
import blockchain
import threading
import time
from sqlite import update_turn, save_map_from_memory, save_users_from_memory
from backend import spawn, update_user_data, Boar, get_buildings


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
        self.latest_block = blockchain.last_bis_hash()
        if self.compare_block != self.latest_block:
            self.save_databases()
            self.turn += 1
            self.compare_block = self.latest_block
            update_turn(self.turn)

            for username, user_data in self.usersdb.items():
                print("user (turn engine)", username, user_data)

                updated_values = {}

                # Update action_points and age if "action_points" exists
                if "action_points" in user_data:
                    updated_values["action_points"] = user_data["action_points"] + 5
                    updated_values["age"] = user_data["age"] + 1

                food = user_data["food"]

                # Count farms and barracks, and update peasants
                farms = sum(1 for entry in get_buildings(user_data) if entry.get("type") == "farm")
                barracks = sum(1 for entry in get_buildings(user_data) if entry.get("type") == "barracks")

                updated_values["peasants"] = user_data["peasants"] + min(farms, user_data["pop_lim"])

                # Calculate the maximum number of free_armies that can be produced considering food, peasants, and barracks
                potential_free_army = min(food, updated_values["peasants"], barracks)

                updated_values["free_army"] = user_data.get("free_army", 0) + potential_free_army
                updated_values["food"] = food - potential_free_army
                updated_values["peasants"] -= potential_free_army

                # Increase food by one for every leftover peasant
                updated_values["food"] += updated_values["peasants"]

                # Update the user data once, instead of multiple times
                update_user_data(user=username, updated_values=updated_values, user_data_dict=self.usersdb)

                # Print buildings
                print("buildings", get_buildings(user_data))

            spawn(mapdb=self.mapdb,
                  entity_class=Boar,
                  probability=0.25,
                  size=25,
                  every=5,
                  max_entities=1
                  )

        print(f"Current turn: {self.turn}")

    def run(self):
        while self.running:
            self.check_for_updates()
            interruptible_sleep(30, stop_condition=lambda: not self.running)

    def stop(self):  # Add this method to stop the thread gracefully
        self.running = False


if __name__ == "__main__":
    turn_engine = TurnEngine()
    turn_engine.start()
    print("Turn engine started")
