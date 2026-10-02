import os
import json
import time
from typing import Dict, Any, Optional
from src.perception.types import ApproachState

class GridlockWatchdog:
    """
    Network-level Gridlock Watchdog.
    Monitors downstream queue congestion. If near-capacity threshold is exceeded across all phases
    for > gridlock_watchdog_window_sec (default 60s), flags gridlock warning and triggers
    upstream pressure penalties via Network Coordinator.
    """
    def __init__(
        self,
        junction_id: str,
        near_capacity_threshold: float = 15.0,
        window_sec: float = 60.0,
        pressure_penalty: float = 10.0,
        log_dir: str = "logs"
    ):
        self.junction_id = junction_id
        self.near_capacity_threshold = near_capacity_threshold
        self.window_sec = window_sec
        self.pressure_penalty = pressure_penalty
        self.log_dir = log_dir

        self.consecutive_jam_start: Optional[float] = None
        self.is_gridlock_active: bool = False

        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "gridlock_events.jsonl")

    def update(self, approach_states: Dict[str, ApproachState]) -> Optional[Dict[str, Any]]:
        """
        Scans downstream queue states of all approaches.
        Returns gridlock warning event payload if triggered.
        """
        now = time.time()
        # Check if downstream queue exceeds capacity on monitored links
        is_jammed = any(state.downstream_queue >= self.near_capacity_threshold for state in approach_states.values())

        if is_jammed:
            if self.consecutive_jam_start is None:
                self.consecutive_jam_start = now
            elif (now - self.consecutive_jam_start) >= self.window_sec:
                if not self.is_gridlock_active:
                    self.is_gridlock_active = True
                    event_payload = {
                        "timestamp": now,
                        "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "junction_id": self.junction_id,
                        "event": "GRIDLOCK_WARNING",
                        "pressure_penalty": self.pressure_penalty,
                        "duration_jammed_sec": round(now - self.consecutive_jam_start, 1)
                    }
                    self._log_event(event_payload)
                    return event_payload
        else:
            if self.is_gridlock_active:
                event_payload = {
                    "timestamp": now,
                    "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "junction_id": self.junction_id,
                    "event": "GRIDLOCK_RESOLVED",
                    "duration_jammed_sec": round(now - (self.consecutive_jam_start or now), 1)
                }
                self._log_event(event_payload)
            self.consecutive_jam_start = None
            self.is_gridlock_active = False

        return None

    def _log_event(self, event_payload: Dict[str, Any]):
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event_payload) + "\n")
        except Exception as e:
            print(f"[GridlockWatchdog ERROR] Log write failed: {e}")
