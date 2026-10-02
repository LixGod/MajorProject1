import pytest
import time
from src.control.max_pressure_controller import GapOutTimer

def test_gap_out_timer():
    timer = GapOutTimer(gap_out_threshold_sec=2.0, gap_out_extend_sec=2.0)
    now = time.time()
    timer.record_arrival(now)

    # 1. Before min_green, should never gap out
    assert not timer.should_gap_out(now + 3.0, elapsed_in_phase=5.0, min_green_sec=12.0, has_new_arrivals=False)

    # 2. After min_green, with recent arrival, should not gap out
    assert not timer.should_gap_out(now + 1.0, elapsed_in_phase=15.0, min_green_sec=12.0, has_new_arrivals=False)

    # 3. After min_green, with arrival gap exceeding threshold (3.0s > 2.0s), SHOULD gap out
    assert timer.should_gap_out(now + 3.5, elapsed_in_phase=15.0, min_green_sec=12.0, has_new_arrivals=False)
