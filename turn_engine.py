import asyncio
import blockchain
import threading
import time
from sqlite import update_turn, update_user_data, load_all_user_data

class TurnEngine(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.latest_block = None
        self.compare_block = None
        self.turn = 0
        self.running = True

    def check_for_updates(self):
        while True:
            self.latest_block = blockchain.last_bis_hash()
            if self.compare_block != self.latest_block:
                self.turn += 1
                self.compare_block = self.latest_block
                update_turn(self.turn)

                for username, user_data in load_all_user_data().items():
                    print("user", username, user_data)

                    if "action_points" in user_data:
                        updated_action_points = user_data["action_points"] + 20
                        update_user_data(user=username, updated_values={"action_points": updated_action_points})

            print(f"Current turn: {self.turn}")
            time.sleep(30)

    def run(self):
        while self.running:
            self.check_for_updates()

    def stop(self):  # Add this method to stop the thread gracefully
        self.running = False

if __name__ == "__main__":
    turn_engine = TurnEngine()
    turn_engine.start()
    print("Turn enging started")
