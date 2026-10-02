import pytest
import time
from src.control.signal_controller import SimulationSignalController, SignalState

def test_safety_all_red_transition():
    sim = SimulationSignalController(default_all_red_sec=3.0)
    assert sim.current_state == SignalState.GREEN
    assert sim.current_phase_id == 1

    # Request transition to Phase 2
    sim.set_phase(phase_id=2, active_movements=["east_through"], all_red_duration=3.0)

    # Must immediately enter ALL_RED_CLEARANCE
    state = sim.get_current_state()
    assert state["signal_state"] == SignalState.ALL_RED_CLEARANCE.value
    assert state["in_clearance"] is True

    # Advance time by 1s (less than 3s clearance) -> remains in ALL_RED_CLEARANCE
    sim.tick(1.0, all_red_duration=3.0)
    assert sim.get_current_state()["signal_state"] == SignalState.ALL_RED_CLEARANCE.value

    # Wait for clearance duration to expire
    time.sleep(3.1)
    sim.tick(1.0, all_red_duration=3.0)

    # Now transitions safely to GREEN for Phase 2
    state_after = sim.get_current_state()
    assert state_after["signal_state"] == SignalState.GREEN.value
    assert state_after["phase_id"] == 2
