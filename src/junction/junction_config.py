from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ControlParams(BaseModel):
    min_green_sec: float = 12.0
    max_green_sec: float = 90.0
    all_red_clearance_sec: float = 3.0
    gap_out_threshold_sec: float = 2.0
    gap_out_extend_sec: float = 2.0
    w_veh: float = 1.0
    w_down: float = 0.8
    w_age: float = 0.05
    w_max_wait_sec: float = 120.0
    class_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "car": 1.0,
            "motorcycle": 0.5,
            "auto_rickshaw": 0.5,
            "auto-rickshaw": 0.5,
            "bus": 2.5,
            "truck": 2.5,
            "bicycle": 0.3,
            "pedestrian": 0.0,
            "ambulance": 5.0,
            "fire_truck": 5.0
        }
    )
    saturation_flow_rate_veh_per_sec_per_lane: float = 0.5

class LocationConfig(BaseModel):
    latitude: float = 19.0760
    longitude: float = 72.8777
    source: str = "tomtom"
    address: Optional[str] = "Mumbai, Maharashtra, India"

class ApproachConfig(BaseModel):
    id: str
    lanes: int = 3
    camera_source: str = "synthetic"
    movements: List[str] = Field(default_factory=lambda: ["through", "left", "right"])
    downstream_link_id: Optional[str] = None
    roi: List[List[float]] = Field(default_factory=list)
    stop_line: List[List[float]] = Field(default_factory=list)

class JunctionConfig(BaseModel):
    junction_id: str
    name: str
    num_approaches: int
    location: LocationConfig = Field(default_factory=LocationConfig)
    approaches: List[ApproachConfig]
    phase_conflict_matrix: str = "auto"
    pedestrian_phases: bool = False
    control_params: ControlParams = Field(default_factory=ControlParams)
