import pytest
import time
from src.control.gridlock_watchdog import GridlockWatchdog
from src.perception.types import ApproachState

def test_gridlock_watchdog_warning():
    dog = GridlockWatchdog(junction_id="j1", near_capacity_threshold=10.0, window_sec=0.5, pressure_penalty=5.0)

    states = {
        "north": ApproachState("north", 5.0, 5, downstream_queue=15.0, wait_since_green=10.0)
    }

    # Initial update
    evt1 = dog.update(states)
    assert evt1 is None  # Not elapsed window yet

    time.sleep(0.6)
    evt2 = dog.update(states)
    assert evt2 is not None
    assert evt2["event"] == "GRIDLOCK_WARNING"
    assert evt2["pressure_penalty"] == 5.0
