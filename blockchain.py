import requests
import json
import time

def last_bis_hash():
    url = "https://bismuth.im/api/node/blocklast"
    retries = 3
    backoff_factor = 1.5
    timeout = 5  # set a reasonable timeout

    for i in range(retries):
        try:
            last_block_raw = requests.get(url=url, timeout=timeout).text
            last_block = json.loads(last_block_raw)["block_hash"]
            return last_block
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"Attempt {i + 1} failed. Error: {e}")
            if i < retries - 1:  # No delay after the last attempt
                sleep_time = backoff_factor * (2 ** i)
                print(f"Waiting {sleep_time} seconds before retrying.")
                time.sleep(sleep_time)
        except json.JSONDecodeError:
            print("Failed to decode JSON. Unexpected response format.")
            break
    return None  # Return None or a default value if all attempts fail

if __name__ == "__main__":
    print(last_bis_hash())
