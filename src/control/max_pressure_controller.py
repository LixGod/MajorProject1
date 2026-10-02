from typing import Dict, List, Tuple, Optional, Any
from src.perception.types import ApproachState
from src.junction.junction_config import ControlParams
from src.junction.phase_builder import PhaseGroup

def compute_pressure(approach_state: ApproachState, params: ControlParams) -> float:
    """
    Computes Max-Pressure score for a single approach:
    pressure = w_veh * queue_length - w_down * downstream_queue + w_age * wait_since_green
    """
    p = (params.w_veh * approach_state.queue_length
         - params.w_down * approach_state.downstream_queue
         + params.w_age * approach_state.wait_since_green)
    return p

class GapOutTimer:
    """
    Actuated Gap-Out timer: while phase is green, extends green duration by gap_out_extend_sec
    when new arrivals are detected within gap_out_threshold_sec, up to max_green_sec.
    Triggers early phase termination if no arrivals occur within threshold after min_green_sec.
    """
    def __init__(self, gap_out_threshold_sec: float = 2.0, gap_out_extend_sec: float = 2.0):
        self.gap_out_threshold_sec = gap_out_threshold_sec
        self.gap_out_extend_sec = gap_out_extend_sec
        self.last_arrival_time: float = 0.0

    def record_arrival(self, current_time: float):
        self.last_arrival_time = current_time

    def should_gap_out(
        self,
        current_time: float,
        elapsed_in_phase: float,
        min_green_sec: float,
        has_new_arrivals: bool
    ) -> bool:
        if elapsed_in_phase < min_green_sec:
            return False  # Never gap-out before min_green_sec

        if has_new_arrivals:
            self.last_arrival_time = current_time
            return False

        time_since_arrival = current_time - self.last_arrival_time
        return time_since_arrival > self.gap_out_threshold_sec

def select_phase(
    candidate_phases: List[PhaseGroup],
    approach_states: Dict[str, ApproachState],
    params: ControlParams,
    current_phase_id: int,
    elapsed_in_current_phase: float
) -> Tuple[PhaseGroup, float, bool]:
    """
    Selects the next optimal phase using Max-Pressure with aging & starvation override.
    Returns: (selected_phase, computed_green_duration, is_starvation_override)
    """
    # 1. Enforce min_green_sec constraint on current phase
    if elapsed_in_current_phase < params.min_green_sec:
        current_pg = next((p for p in candidate_phases if p.phase_id == current_phase_id), candidate_phases[0])
        g_dur = compute_green_duration(current_pg, approach_states, params)
        return current_pg, g_dur, False

    # 2. Hard Starvation Override Check
    starved_approach = None
    for app_id, state in approach_states.items():
        if state.wait_since_green >= params.w_max_wait_sec:
            starved_approach = app_id
            print(f"[MaxPressureController] STARVATION OVERRIDE triggered for approach '{app_id}' (wait: {state.wait_since_green:.1f}s)")
            break

    if starved_approach:
        for pg in candidate_phases:
            if any(m.startswith(starved_approach) for m in pg.movements):
                g_dur = compute_green_duration(pg, approach_states, params)
                return pg, g_dur, True

    # 3. Calculate pressure score for each phase
    best_phase = candidate_phases[0]
    max_phase_pressure = -float("inf")

    for pg in candidate_phases:
        phase_pressure = 0.0
        for m_key in pg.movements:
            app_id = m_key.split("_")[0]
            if app_id in approach_states:
                phase_pressure += compute_pressure(approach_states[app_id], params)

        if phase_pressure > max_phase_pressure:
            max_phase_pressure = phase_pressure
            best_phase = pg

    green_duration = compute_green_duration(best_phase, approach_states, params)
    return best_phase, green_duration, False

def compute_green_duration(
    selected_phase: PhaseGroup,
    approach_states: Dict[str, ApproachState],
    params: ControlParams
) -> float:
    """
    g = clip(base + k * (total weighted queue / saturation_flow_rate), min_green_sec, max_green_sec)
    """
    total_weighted_queue = 0.0
    for m_key in selected_phase.movements:
        app_id = m_key.split("_")[0]
        if app_id in approach_states:
            total_weighted_queue += approach_states[app_id].queue_length

    sat_rate = max(0.1, params.saturation_flow_rate_veh_per_sec_per_lane)
    raw_duration = params.min_green_sec + (total_weighted_queue / sat_rate)
    
    # Clip to [min_green_sec, max_green_sec]
    clipped_duration = max(params.min_green_sec, min(params.max_green_sec, raw_duration))
    return float(clipped_duration)
