import asyncio
import blockchain
import threading
import time
from sqlite import update_turn, save_map_from_memory, save_users_from_memory
from backend import spawn, update_user_data, Boar


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
                print("user", username, user_data)

                if "action_points" in user_data:
                    update_user_data(user=username,
                                     updated_values={"action_points": user_data["action_points"] + 5,
                                                     "age": user_data["age"] + 1},
                                     user_data_dict=self.usersdb)

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
