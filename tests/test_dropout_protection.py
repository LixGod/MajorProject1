import pytest
import time
from src.perception.approach_state_tracker import ApproachStateTracker
from src.perception.types import Detection

def test_camera_dropout_decay_and_health_flag():
    tracker = ApproachStateTracker(
        approach_id="north",
        roi_polygon=[[0, 0], [100, 0], [100, 100], [0, 100]],
        stop_line=[[0, 50], [100, 50]],
        class_weights={"car": 1.0},
        dropout_decay_rate=0.8,
        dropout_timeout_sec=0.1
    )

    det = Detection(track_id=1, class_id=4, class_name="car", confidence=0.9, bbox=(10, 10, 20, 20))
    st1 = tracker.update([det], is_green=False, dt_sec=1.0)
    assert st1.queue_length == 1.0
    assert st1.feed_healthy is True

    # Simulate camera dropout
    time.sleep(0.2)
    st2 = tracker.update([], is_green=False, dt_sec=1.0)
    assert st2.feed_healthy is False
    # Queue length should decay (0.8 * 1.0 = 0.8) rather than jumping straight to 0.0
    assert abs(st2.queue_length - 0.8) < 1e-3
