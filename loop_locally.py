"""
loop_locally.py
----------------
For LOCAL TESTING ONLY - runs collector.py's collect_once() every N minutes
while this script is running. Good for watching data build up before we
automate everything with GitHub Actions.

Run with:
    python loop_locally.py

Stop with Ctrl+C.
"""

import time
from collector import collect_once

INTERVAL_MINUTES = 5

if __name__ == "__main__":
    print(f"Collecting every {INTERVAL_MINUTES} minutes. Press Ctrl+C to stop.")
    while True:
        collect_once()
        time.sleep(INTERVAL_MINUTES * 60)
