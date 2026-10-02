import asyncio
import os
import json
import time
from typing import Dict, List, Any, Optional
from src.junction.junction_config import JunctionConfig
from src.junction.phase_builder import JunctionTopology, PhaseGroup
from src.perception.types import Detection, Frame, ApproachState
from src.perception.approach_state_tracker import ApproachStateTracker
from src.control.signal_controller import SignalController, SimulationSignalController, SignalState
from src.control.max_pressure_controller import select_phase, compute_green_duration, GapOutTimer, compute_pressure
from src.control.preemption import PreemptionHandler
from src.control.gridlock_watchdog import GridlockWatchdog
from src.network.coordinator import global_coordinator

class JunctionRuntime:
    """
    Async Control Loop Orchestration per Junction.
    Executes 1s control ticks: state updates, preemption checks, gap-out timer checks,
    Max-Pressure phase selection, signal transitions, WebSocket broadcasting, and log emission.
    """
    def __init__(self, config: JunctionConfig, signal_controller: Optional[SignalController] = None):
        self.config = config
        self.junction_id = config.junction_id
        self.signal_controller = signal_controller or SimulationSignalController(
            default_all_red_sec=config.control_params.all_red_clearance_sec
        )

        # Build topology & phases
        movements_map = {app.id: app.movements for app in config.approaches}
        app_ids = [app.id for app in config.approaches]
        self.topology = JunctionTopology(app_ids, movements_map)
        self.phases: List[PhaseGroup] = self.topology.build_phases()

        # Build per-approach trackers
        self.trackers: Dict[str, ApproachStateTracker] = {}
        for app in config.approaches:
            self.trackers[app.id] = ApproachStateTracker(
                approach_id=app.id,
                roi_polygon=app.roi,
                stop_line=app.stop_line,
                class_weights=config.control_params.class_weights
            )

        self.current_phase = self.phases[0]
        self.current_green_duration = config.control_params.min_green_sec
        self.phase_start_time = time.time()
        self.gap_out_timer = GapOutTimer(
            gap_out_threshold_sec=config.control_params.gap_out_threshold_sec,
            gap_out_extend_sec=config.control_params.gap_out_extend_sec
        )

        self.preemption_handler = PreemptionHandler(self.junction_id)
        self.gridlock_watchdog = GridlockWatchdog(self.junction_id)
        
        self.latest_approach_states: Dict[str, ApproachState] = {}
        self.manual_override_phase_id: Optional[int] = None
        self.audit_logs: List[Dict[str, Any]] = []
        
        os.makedirs("logs", exist_ok=True)
        self.state_log_file = os.path.join("logs", f"{self.junction_id}_states.jsonl")

    def set_manual_override(self, phase_id: int, operator_id: str = "operator_1", reason: str = "Manual override request"):
        """Forces phase transition with mandatory audit log."""
        self.manual_override_phase_id = phase_id
        log_entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "junction_id": self.junction_id,
            "operator_id": operator_id,
            "forced_phase_id": phase_id,
            "reason": reason
        }
        self.audit_logs.append(log_entry)
        print(f"[JunctionRuntime AUDIT LOG] Manual override by {operator_id} for Phase {phase_id}: {reason}")

    def clear_manual_override(self):
        self.manual_override_phase_id = None

    async def tick(self, per_approach_detections: Dict[str, List[Detection]], dt_sec: float = 1.0) -> Dict[str, Any]:
        now = time.time()
        elapsed_in_phase = now - self.phase_start_time

        # Update HAL simulation timer
        if isinstance(self.signal_controller, SimulationSignalController):
            self.signal_controller.tick(dt_sec, all_red_duration=self.config.control_params.all_red_clearance_sec)

        # 1. Update per-approach state trackers
        states: Dict[str, ApproachState] = {}
        for app in self.config.approaches:
            app_id = app.id
            is_green = any(m.startswith(app_id) for m in self.current_phase.movements)
            downstream_q = global_coordinator.get_downstream_queue(app.downstream_link_id)
            dets = per_approach_detections.get(app_id, [])

            state = self.trackers[app_id].update(dets, is_green, dt_sec, downstream_q)
            states[app_id] = state

            # Publish queue state for upstream neighbors
            if app.downstream_link_id:
                global_coordinator.publish_link_state(app.downstream_link_id, state.queue_length)

        self.latest_approach_states = states

        # 2. Check for emergency vehicle preemption
        emerg_app = self.preemption_handler.check_preemption(states)
        if emerg_app and not self.preemption_handler.active_preemption:
            self.preemption_handler.trigger_preemption(emerg_app, states[emerg_app].emergency_class or "ambulance")

        # Handle Preemption Execution Path
        if self.preemption_handler.active_preemption:
            if self.preemption_handler.should_clear_preemption(states):
                self.preemption_handler.clear_preemption()
            else:
                # Find phase serving emergency approach
                target_app = self.preemption_handler.target_approach_id
                emerg_phase = next(
                    (p for p in self.phases if any(m.startswith(target_app) for m in p.movements)),
                    self.phases[0]
                )
                if self.current_phase.phase_id != emerg_phase.phase_id:
                    self.current_phase = emerg_phase
                    self.phase_start_time = now
                    self.signal_controller.set_phase(
                        emerg_phase.phase_id, emerg_phase.movements, self.config.control_params.all_red_clearance_sec
                    )

        # 3. Check for Gridlock Watchdog
        watchdog_event = self.gridlock_watchdog.update(states)
        if watchdog_event and watchdog_event.get("event") == "GRIDLOCK_WARNING":
            for app in self.config.approaches:
                if app.downstream_link_id:
                    global_coordinator.publish_gridlock_warning(
                        self.junction_id, app.downstream_link_id, self.gridlock_watchdog.pressure_penalty
                    )

        # 4. Check Manual Override
        if self.manual_override_phase_id is not None:
            override_pg = next((p for p in self.phases if p.phase_id == self.manual_override_phase_id), None)
            if override_pg and override_pg.phase_id != self.current_phase.phase_id:
                self.current_phase = override_pg
                self.phase_start_time = now
                self.signal_controller.set_phase(
                    override_pg.phase_id, override_pg.movements, self.config.control_params.all_red_clearance_sec
                )

        # 5. Normal Max-Pressure Phase Selection & Gap-Out Logic
        elif not self.preemption_handler.active_preemption:
            has_new_arrivals = any(s.raw_vehicle_count > 0 for s in states.values())
            should_gap = self.gap_out_timer.should_gap_out(
                now, elapsed_in_phase, self.config.control_params.min_green_sec, has_new_arrivals
            )
            max_green_reached = elapsed_in_phase >= self.current_green_duration

            if max_green_reached or should_gap:
                next_phase, g_dur, is_starvation = select_phase(
                    self.phases, states, self.config.control_params, self.current_phase.phase_id, elapsed_in_phase
                )
                if next_phase.phase_id != self.current_phase.phase_id:
                    self.current_phase = next_phase
                    self.current_green_duration = g_dur
                    self.phase_start_time = now
                    self.signal_controller.set_phase(
                        next_phase.phase_id, next_phase.movements, self.config.control_params.all_red_clearance_sec
                    )

        # 6. Build current state payload for WebSocket & dashboard
        hal_state = self.signal_controller.get_current_state()
        remaining_time = max(0.0, self.current_green_duration - (now - self.phase_start_time))

        pressures: Dict[str, float] = {
            app_id: compute_pressure(st, self.config.control_params) for app_id, st in states.items()
        }

        telemetry = {
            "timestamp": now,
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "junction_id": self.junction_id,
            "junction_name": self.config.name,
            "current_phase": {
                "id": self.current_phase.phase_id,
                "name": self.current_phase.name,
                "movements": self.current_phase.movements
            },
            "signal_state": hal_state["signal_state"],
            "in_all_red_clearance": hal_state["in_clearance"],
            "remaining_green_sec": round(remaining_time, 1),
            "total_green_sec": round(self.current_green_duration, 1),
            "approach_states": {
                app_id: {
                    "queue_length": round(st.queue_length, 2),
                    "raw_count": st.raw_vehicle_count,
                    "downstream_queue": round(st.downstream_queue, 2),
                    "wait_since_green_sec": round(st.wait_since_green, 1),
                    "pressure": round(pressures[app_id], 2),
                    "feed_healthy": st.feed_healthy,
                    "is_emergency": st.is_emergency,
                    "category_counts": st.category_counts
                } for app_id, st in states.items()
            },
            "alerts": {
                "preemption_active": self.preemption_handler.active_preemption,
                "preemption_approach": self.preemption_handler.target_approach_id,
                "gridlock_warning": self.gridlock_watchdog.is_gridlock_active,
                "manual_override_active": self.manual_override_phase_id is not None
            }
        }

        # Log state entry to disk for offline evaluation
        try:
            with open(self.state_log_file, "a") as f:
                f.write(json.dumps(telemetry) + "\n")
        except Exception:
            pass

        return telemetry
