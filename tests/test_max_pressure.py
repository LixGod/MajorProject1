import pytest
from src.perception.types import ApproachState
from src.junction.junction_config import ControlParams
from src.junction.phase_builder import PhaseGroup
from src.control.max_pressure_controller import compute_pressure, select_phase, compute_green_duration

def test_compute_pressure():
    params = ControlParams(w_veh=1.0, w_down=0.8, w_age=0.05)
    st = ApproachState(
        approach_id="north",
        queue_length=10.0,
        raw_vehicle_count=10,
        downstream_queue=2.0,
        wait_since_green=40.0
    )
    # pressure = 1.0 * 10 - 0.8 * 2 + 0.05 * 40 = 10 - 1.6 + 2.0 = 10.4
    p = compute_pressure(st, params)
    assert abs(p - 10.4) < 1e-5

def test_starvation_override():
    params = ControlParams(w_max_wait_sec=120.0)
    pg1 = PhaseGroup(phase_id=1, name="P1", movements=["north_through", "south_through"])
    pg2 = PhaseGroup(phase_id=2, name="P2", movements=["east_through", "west_through"])

    states = {
        "north": ApproachState("north", 2.0, 2, 0.0, 10.0),
        "south": ApproachState("south", 2.0, 2, 0.0, 10.0),
        "east": ApproachState("east", 1.0, 1, 0.0, 130.0),  # Starved (> 120s)
        "west": ApproachState("west", 1.0, 1, 0.0, 130.0)
    }

    selected, dur, is_override = select_phase([pg1, pg2], states, params, current_phase_id=1, elapsed_in_current_phase=15.0)
    assert is_override is True
    assert selected.phase_id == 2
