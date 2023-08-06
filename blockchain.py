import requests
import json


def last_bis_hash():
    url = "https://bismuth.im/api/node/blocklast"

    last_block_raw = requests.get(url=url).text
    last_block = json.loads(last_block_raw)["block_hash"]
    return last_block


if __name__ == "__main__":
    print(last_bis_hash())
