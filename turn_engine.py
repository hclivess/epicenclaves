import asyncio
import random

import blockchain
import threading
import time
from sqlite import update_turn, save_map_from_memory, save_users_from_memory
from backend import spawn, update_user_data, Boar, get_buildings, hashify
import string

TEST = False


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
        self.update_block()

        if self.compare_block != self.latest_block:
            self.perform_turn_updates()

            for username, user_data in self.usersdb.items():
                self.process_user_turn_updates(username, user_data)

            self.spawn_entities()

        print(f"Current turn: {self.turn}")

    def update_block(self):
        if TEST:
            self.latest_block = hashify(fake_hash())
        else:
            self.latest_block = blockchain.last_bis_hash()

    def perform_turn_updates(self):
        self.save_databases()
        self.turn += 1
        self.compare_block = self.latest_block
        update_turn(self.turn)

    def process_user_turn_updates(self, username, user_data):
        print("user (turn engine)", username, user_data)
        updated_values = self.calculate_user_updates(user_data)

        # Update the user data once
        update_user_data(
            user=username,
            updated_values=updated_values,
            user_data_dict=self.usersdb,
        )

        # Print buildings
        print("buildings", get_buildings(user_data))

    def calculate_user_updates(self, user_data):
        updated_values = {}

        if "action_points" in user_data:
            updated_values["action_points"] = user_data["action_points"] + 5
            updated_values["age"] = user_data["age"] + 1

        army_deployed = user_data.get("army_deployed", 0)
        food = user_data["food"]

        farms, barracks = self.count_farms_and_barracks(user_data)
        potential_army_free = self.calculate_potential_army_free(food, user_data, barracks, army_deployed)
        potential_peasants_addition = self.calculate_potential_peasants_addition(farms, user_data, potential_army_free,
                                                                                 army_deployed)

        updated_values.update({
            "army_free": user_data.get("army_free", 0) + potential_army_free,
            "peasants": user_data["peasants"] + potential_peasants_addition,
            "food": food - 2 * (potential_army_free + army_deployed) + potential_peasants_addition
        })

        return updated_values

    def count_farms_and_barracks(self, user_data):
        farms = sum(1 for entry in get_buildings(user_data) if entry.get("type") == "farm")
        barracks = sum(1 for entry in get_buildings(user_data) if entry.get("type") == "barracks")
        return farms, barracks

    def calculate_potential_army_free(self, food, user_data, barracks, army_deployed):
        return min(food, user_data["peasants"], barracks) - army_deployed

    def calculate_potential_peasants_addition(self, farms, user_data, potential_army_free, army_deployed):
        return min(farms, user_data["pop_lim"] - (user_data["peasants"] + potential_army_free + army_deployed))

    def spawn_entities(self):
        spawn(
            mapdb=self.mapdb,
            entity_class=Boar,
            probability=0.25,
            size=25,
            every=5,
            max_entities=1,
        )

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
