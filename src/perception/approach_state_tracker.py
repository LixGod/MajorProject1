import time
import math
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import cv2
from src.perception.types import Detection, ApproachState

def is_point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    """Checks if a point (x, y) is inside a polygon [[x1, y1], [x2, y2], ...]"""
    pts = np.array(polygon, dtype=np.int32)
    res = cv2.pointPolygonTest(pts, (float(point[0]), float(point[1])), False)
    return res >= 0

class ApproachStateTracker:
    """
    Per-approach vehicle queue & state tracker.
    Consumes detections per frame, filters by ROI polygon, handles camera dropouts safely with decay,
    and updates wait times.
    """
    def __init__(
        self,
        approach_id: str,
        roi_polygon: List[List[float]],
        stop_line: List[List[float]],
        class_weights: Dict[str, float],
        dropout_decay_rate: float = 0.90,
        dropout_timeout_sec: float = 3.0
    ):
        self.approach_id = approach_id
        self.roi_polygon = roi_polygon
        self.stop_line = stop_line
        self.class_weights = class_weights
        self.dropout_decay_rate = dropout_decay_rate
        self.dropout_timeout_sec = dropout_timeout_sec

        self.last_valid_queue_length: float = 0.0
        self.last_valid_count: int = 0
        self.last_update_time: float = time.time()
        self.wait_since_green: float = 0.0
        self.feed_healthy: bool = True

    def update(
        self,
        detections: List[Detection],
        is_green: bool,
        dt_sec: float,
        downstream_queue: float = 0.0
    ) -> ApproachState:
        now = time.time()
        
        if is_green:
            self.wait_since_green = 0.0
        else:
            self.wait_since_green += dt_sec

        # Filter detections inside ROI
        roi_detections = []
        is_emergency = False
        emergency_class = None
        category_counts: Dict[str, int] = {"LMV": 0, "HMV": 0, "Auto Rickshaw": 0, "Motorcycle": 0, "Pedestrian": 0}

        for det in detections:
            bbox = det.bbox
            center_x = (bbox[0] + bbox[2]) / 2.0
            center_y = (bbox[1] + bbox[3]) / 2.0

            if self.roi_polygon and len(self.roi_polygon) >= 3:
                inside = is_point_in_polygon((center_x, center_y), self.roi_polygon)
            else:
                inside = True  # Fallback to whole frame if ROI not specified

            if inside:
                roi_detections.append(det)
                cname = det.class_name.lower()

                if cname in ["ambulance", "fire_truck"] or "emergency" in cname:
                    is_emergency = True
                    emergency_class = det.class_name

                if cname in ["car", "taxi", "lmv"]:
                    category_counts["LMV"] += 1
                elif cname in ["bus", "truck", "hmv"]:
                    category_counts["HMV"] += 1
                elif cname in ["auto-rickshaw", "auto_rickshaw", "rickshaw"]:
                    category_counts["Auto Rickshaw"] += 1
                elif cname in ["motorcycle", "rider", "two_wheeler"]:
                    category_counts["Motorcycle"] += 1
                elif cname in ["pedestrian", "person"]:
                    category_counts["Pedestrian"] += 1

        # Check for camera feed dropout
        if detections is None or (len(detections) == 0 and (now - self.last_update_time) > self.dropout_timeout_sec):
            self.feed_healthy = False
            # Decay last queue estimate instead of collapsing to zero
            self.last_valid_queue_length *= self.dropout_decay_rate
            self.last_valid_count = int(self.last_valid_queue_length)
        else:
            self.feed_healthy = True
            self.last_update_time = now

            # Compute weighted queue length
            weighted_queue = 0.0
            for det in roi_detections:
                w = self.class_weights.get(det.class_name.lower(), 1.0)
                weighted_queue += w

            self.last_valid_queue_length = weighted_queue
            self.last_valid_count = len(roi_detections)

        return ApproachState(
            approach_id=self.approach_id,
            queue_length=max(0.0, float(self.last_valid_queue_length)),
            raw_vehicle_count=self.last_valid_count,
            downstream_queue=downstream_queue,
            wait_since_green=self.wait_since_green,
            is_emergency=is_emergency,
            emergency_class=emergency_class,
            feed_healthy=self.feed_healthy,
            last_update_time=now,
            category_counts=category_counts
        )
