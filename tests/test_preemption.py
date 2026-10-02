import pytest
import time
from src.control.preemption import PreemptionHandler
from src.perception.types import ApproachState

def test_emergency_preemption_trigger_and_clear():
    handler = PreemptionHandler(junction_id="test_j1", max_preemption_hold_sec=10.0)

    states = {
        "north": ApproachState("north", 5.0, 5, 0.0, 10.0, is_emergency=True, emergency_class="ambulance"),
        "south": ApproachState("south", 2.0, 2, 0.0, 10.0)
    }

    emerg_app = handler.check_preemption(states)
    assert emerg_app == "north"

    handler.trigger_preemption("north", "ambulance")
    assert handler.active_preemption is True

    # Vehicle passes -> emergency cleared
    states["north"].is_emergency = False
    assert handler.should_clear_preemption(states) is True

    handler.clear_preemption()
    assert handler.active_preemption is False
