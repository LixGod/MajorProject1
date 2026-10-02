import time
from typing import Dict, Any, Optional

class NetworkCoordinator:
    """
    In-process Network Coordinator for cross-junction communication.
    Allows junctions to exchange downstream link queue states and coordinate gridlock/preemption events.
    """
    def __init__(self):
        # Store queue state per link: link_id -> queue_length
        self.link_queues: Dict[str, float] = {}
        # Active gridlock penalties: link_id -> pressure_penalty
        self.gridlock_penalties: Dict[str, float] = {}
        # Preemption status per link
        self.preemption_events: Dict[str, Dict[str, Any]] = {}

    def publish_link_state(self, link_id: str, queue_length: float):
        """Published by an incoming approach to notify upstream neighbors of downstream queue."""
        self.link_queues[link_id] = queue_length

    def get_downstream_queue(self, link_id: Optional[str]) -> float:
        """Called by an upstream junction to fetch downstream link queue."""
        if not link_id:
            return 0.0
        return self.link_queues.get(link_id, 0.0)

    def publish_gridlock_warning(self, junction_id: str, affected_link_id: str, penalty: float):
        """Applies a pressure penalty to upstream movements feeding the jammed link."""
        self.gridlock_penalties[affected_link_id] = penalty
        print(f"[NetworkCoordinator] GRIDLOCK PENALTY ({penalty}) applied to link '{affected_link_id}' from junction '{junction_id}'")

    def resolve_gridlock(self, affected_link_id: str):
        if affected_link_id in self.gridlock_penalties:
            del self.gridlock_penalties[affected_link_id]
            print(f"[NetworkCoordinator] GRIDLOCK RESOLVED on link '{affected_link_id}'")

    def get_gridlock_penalty(self, link_id: Optional[str]) -> float:
        if not link_id:
            return 0.0
        return self.gridlock_penalties.get(link_id, 0.0)

# Global shared instance for single-process runtime
global_coordinator = NetworkCoordinator()
