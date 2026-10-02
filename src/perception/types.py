from dataclasses import dataclass, field
from typing import Protocol, List, Tuple, Dict, Any, Optional
import time

@dataclass
class Detection:
    track_id: Optional[int]
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    timestamp: float = field(default_factory=time.time)

@dataclass
class Frame:
    image: Any  # numpy array (H, W, C)
    timestamp: float
    camera_id: str
    width: int
    height: int

class DetectionProvider(Protocol):
    async def detect(self, frame: Frame) -> List[Detection]:
        """Runs detection on a given frame and returns a list of Detections."""
        ...

@dataclass
class ApproachState:
    approach_id: str
    queue_length: float  # class-weighted queue length in ROI
    raw_vehicle_count: int
    downstream_queue: float
    wait_since_green: float  # seconds since last green phase
    is_emergency: bool = False
    emergency_class: Optional[str] = None
    feed_healthy: bool = True
    last_update_time: float = field(default_factory=time.time)
    category_counts: Dict[str, int] = field(default_factory=dict)
