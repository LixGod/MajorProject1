from abc import ABC, abstractmethod
from enum import Enum
import time
from typing import Dict, Any, Optional, List

class SignalState(str, Enum):
    GREEN = "GREEN"
    ALL_RED_CLEARANCE = "ALL_RED_CLEARANCE"
    RED = "RED"

class SignalController(ABC):
    """
    Hardware Abstraction Layer (HAL) interface for traffic signal hardware / simulation.
    """
    @abstractmethod
    def set_phase(self, phase_id: int, active_movements: List[str], all_red_duration: float = 3.0):
        """Transitions current signal phase to a new phase safely."""
        pass

    @abstractmethod
    def get_current_state(self) -> Dict[str, Any]:
        """Returns the current signal phase and state."""
        pass

class SimulationSignalController(SignalController):
    """
    Simulation-only Signal Controller (DEFAULT implementation).
    Enforces mandatory GREEN -> ALL_RED_CLEARANCE -> NEXT_GREEN transition invariant.
    """
    def __init__(self, default_all_red_sec: float = 3.0):
        self.current_phase_id: int = 1
        self.active_movements: List[str] = []
        self.current_state: SignalState = SignalState.GREEN
        self.default_all_red_sec: float = default_all_red_sec
        self.state_start_time: float = time.time()
        self.transition_in_progress: bool = False
        self.target_phase_id: Optional[int] = None
        self.target_movements: List[str] = []

    def set_phase(self, phase_id: int, active_movements: List[str], all_red_duration: float = 3.0):
        if phase_id == self.current_phase_id and self.current_state == SignalState.GREEN:
            self.active_movements = active_movements
            return

        # Mandate ALL_RED_CLEARANCE phase transition
        self.current_state = SignalState.ALL_RED_CLEARANCE
        self.transition_in_progress = True
        self.target_phase_id = phase_id
        self.target_movements = active_movements
        self.state_start_time = time.time()
        print(f"[HAL SimulationSignalController] Initiating ALL_RED_CLEARANCE ({all_red_duration}s) before Phase {phase_id}")

    def tick(self, dt_sec: float, all_red_duration: float = 3.0):
        """Called every tick of the control runtime to advance clearance timers."""
        if self.transition_in_progress and self.current_state == SignalState.ALL_RED_CLEARANCE:
            elapsed = time.time() - self.state_start_time
            if elapsed >= all_red_duration:
                self.current_phase_id = self.target_phase_id or self.current_phase_id
                self.active_movements = self.target_movements
                self.current_state = SignalState.GREEN
                self.transition_in_progress = False
                self.state_start_time = time.time()
                print(f"[HAL SimulationSignalController] Transition Complete -> Phase {self.current_phase_id} is GREEN")

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "phase_id": self.current_phase_id,
            "active_movements": self.active_movements,
            "signal_state": self.current_state.value,
            "in_clearance": self.transition_in_progress,
            "elapsed_in_state": time.time() - self.state_start_time
        }

class HardwareSignalController(SignalController):
    """
    Hardware Signal Controller (Stub for physical field deployments).
    Must pass explicit safety interlocks before sending GPIO/NEMA/170 serial signals.
    """
    def __init__(self, hardware_interface_url: str = "gpio://localhost"):
        self.hardware_interface_url = hardware_interface_url
        self.sim_fallback = SimulationSignalController()

    def set_phase(self, phase_id: int, active_movements: List[str], all_red_duration: float = 3.0):
        print(f"[HardwareSignalController] SAFETY INTERLOCK: Sending hardware pulse for Phase {phase_id} via {self.hardware_interface_url}")
        self.sim_fallback.set_phase(phase_id, active_movements, all_red_duration)

    def get_current_state(self) -> Dict[str, Any]:
        return self.sim_fallback.get_current_state()
