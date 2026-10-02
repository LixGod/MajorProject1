import os
import json
import time
from typing import Dict, Optional, Tuple, Any
from src.perception.types import ApproachState
from src.junction.phase_builder import PhaseGroup

class PreemptionHandler:
    """
    Emergency Vehicle Preemption Handler.
    Listens for emergency vehicles, interrupts normal scheduling, mandates ALL_RED_CLEARANCE transition,
    holds preemption until cleared or max hold timeout, and logs events for paper evaluation.
    """
    def __init__(self, junction_id: str, max_preemption_hold_sec: float = 45.0, log_dir: str = "logs"):
        self.junction_id = junction_id
        self.max_preemption_hold_sec = max_preemption_hold_sec
        self.log_dir = log_dir
        self.active_preemption: bool = False
        self.preemption_start_time: float = 0.0
        self.target_approach_id: Optional[str] = None
        self.emergency_type: Optional[str] = None

        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "preemption_events.jsonl")

    def check_preemption(self, approach_states: Dict[str, ApproachState]) -> Optional[str]:
        """Scans approaches for emergency vehicles."""
        for app_id, state in approach_states.items():
            if state.is_emergency:
                return app_id
        return None

    def trigger_preemption(self, approach_id: str, emergency_type: str = "ambulance"):
        self.active_preemption = True
        self.preemption_start_time = time.time()
        self.target_approach_id = approach_id
        self.emergency_type = emergency_type
        print(f"[PreemptionHandler EMERGENCY] Preemption triggered for Junction '{self.junction_id}', Approach '{approach_id}' ({emergency_type})")

    def should_clear_preemption(self, approach_states: Dict[str, ApproachState]) -> bool:
        if not self.active_preemption or not self.target_approach_id:
            return True

        elapsed = time.time() - self.preemption_start_time
        if elapsed >= self.max_preemption_hold_sec:
            print(f"[PreemptionHandler] Preemption max hold timeout ({self.max_preemption_hold_sec}s) reached.")
            return True

        target_state = approach_states.get(self.target_approach_id)
        if target_state and not target_state.is_emergency:
            print(f"[PreemptionHandler] Emergency vehicle cleared approach '{self.target_approach_id}'.")
            return True

        return False

    def clear_preemption(self):
        if self.active_preemption:
            duration = time.time() - self.preemption_start_time
            self.log_event(duration)
            self.active_preemption = False
            self.target_approach_id = None
            self.emergency_type = None

    def log_event(self, duration_sec: float):
        event = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "junction_id": self.junction_id,
            "approach_id": self.target_approach_id,
            "emergency_type": self.emergency_type,
            "hold_duration_sec": round(duration_sec, 2)
        }
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"[PreemptionHandler ERROR] Failed to write preemption log: {e}")
