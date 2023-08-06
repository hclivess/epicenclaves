import time

import blockchain


class TurnEngine:
    def __init__(self):

        self.latest_block = None
        self.compare_block = None
        self.turn = 0
        self.go()
        self.block_changed = False  # turn off externally after check

    def go(self):
        while True:
            self.latest_block = blockchain.last_bis_hash()
            if self.compare_block != self.latest_block:
                self.turn += 1
                self.compare_block = self.latest_block
                self.block_changed = True

            print(self.latest_block)
            print(self.turn)
            time.sleep(5)


if __name__ == "__main__":
    turn_engine = TurnEngine()
