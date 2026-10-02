import os
from typing import Dict, Any, List, Optional
from src.perception.model_adapter import ModelAdapter
from src.perception.types import Detection, Frame

class DetectorEngine:
    """
    Perception Detector Engine managing primary 'best.pt' and local 'local.pt' models.
    """
    def __init__(self, config: Dict[str, Any]):
        perception_cfg = config.get("perception", {})
        primary_model = perception_cfg.get("model", "best.pt")
        conf = perception_cfg.get("confidence_threshold", 0.35)
        iou = perception_cfg.get("iou_threshold", 0.50)
        imgsz = perception_cfg.get("imgsz", 640)
        device = perception_cfg.get("device", "auto")

        self.primary_adapter = ModelAdapter(
            model_path="best.pt",
            confidence_threshold=conf,
            iou_threshold=iou,
            imgsz=imgsz,
            device=device
        )
        self.local_adapter = ModelAdapter(
            model_path="local.pt",
            confidence_threshold=conf,
            iou_threshold=iou,
            imgsz=imgsz,
            device=device
        )
        self.active_model_name = primary_model

    async def detect_frame(self, frame: Frame, model_choice: str = "best.pt") -> List[Detection]:
        if "local" in model_choice.lower():
            return await self.local_adapter.detect(frame)
        return await self.primary_adapter.detect(frame)

    def draw_annotations(self, image_np, detections: List[Detection]):
        return self.primary_adapter.draw_annotations(image_np, detections)
