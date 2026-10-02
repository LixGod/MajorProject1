import os
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
from src.perception.types import Detection, Frame, DetectionProvider

class ModelAdapter(DetectionProvider):
    """
    Adapter pattern around YOLO/Ultralytics runtime for PyTorch (.pt), ONNX, and TensorRT.
    Supports primary model 'best.pt' and local model 'local.pt'.
    """
    def __init__(
        self,
        model_path: str = "best.pt",
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.50,
        imgsz: int = 640,
        device: str = "cpu",
        class_mapping: Optional[Dict[int, str]] = None
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.device = device
        self.model = None

        self.class_names: Dict[int, str] = class_mapping or {
            0: "pedestrian",
            1: "rider",
            2: "motorcycle",
            3: "auto-rickshaw",
            4: "car",
            5: "truck",
            6: "bus",
            7: "ambulance",
            8: "fire_truck"
        }
        self._load_model()

    def _load_model(self):
        candidate_paths = [
            self.model_path,
            os.path.join("smart_traffic_system", self.model_path),
            "best.pt",
            "local.pt",
            "smart_traffic_system/best.pt",
            "smart_traffic_system/local.pt",
            "smart_traffic_system/yolov8n.pt"
        ]

        target_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                target_path = p
                break

        if not target_path:
            print(f"[ModelAdapter WARNING] Model weight file not found for '{self.model_path}'. Running in dummy mode.")
            self.model = None
            return

        try:
            from ultralytics import YOLO
            self.model = YOLO(target_path)
            if hasattr(self.model, "names") and isinstance(self.model.names, dict):
                for cid, name in self.model.names.items():
                    if cid not in self.class_names:
                        self.class_names[cid] = str(name)
            print(f"[ModelAdapter] Successfully loaded model weights from '{target_path}' on device '{self.device}'")
        except Exception as e:
            print(f"[ModelAdapter ERROR] Failed to load model weights: {e}")
            self.model = None

    async def detect(self, frame: Frame) -> List[Detection]:
        if self.model is None or frame.image is None:
            return []

        try:
            results = self.model.predict(
                source=frame.image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False
            )
            detections: List[Detection] = []
            if results and len(results) > 0:
                res = results[0]
                boxes = res.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        box = boxes[i]
                        xyxy = box.xyxy[0].cpu().numpy().tolist()
                        conf = float(box.conf[0].cpu().numpy())
                        cls_id = int(box.cls[0].cpu().numpy())
                        class_name = self.class_names.get(cls_id, f"class_{cls_id}")

                        detections.append(
                            Detection(
                                track_id=None,
                                class_id=cls_id,
                                class_name=class_name,
                                confidence=conf,
                                bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                                timestamp=frame.timestamp
                            )
                        )
            return detections
        except Exception as e:
            print(f"[ModelAdapter ERROR] Detection inference failed: {e}")
            return []

    def draw_annotations(self, image_np: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Annotates image array with bounding boxes, class labels, and confidence scores."""
        annotated = image_np.copy()
        color_map = {
            "car": (0, 255, 0),
            "auto-rickshaw": (255, 200, 0),
            "motorcycle": (255, 100, 0),
            "bus": (255, 0, 255),
            "truck": (0, 200, 255),
            "ambulance": (0, 0, 255),
            "fire_truck": (0, 0, 255),
            "pedestrian": (200, 200, 200)
        }

        for det in detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            cname = det.class_name.lower()
            color = color_map.get(cname, (0, 255, 0))

            # Bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label box
            label = f"{det.class_name} {det.confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 20)), (x1 + tw + 6, max(20, y1)), color, -1)
            cv2.putText(annotated, label, (x1 + 3, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return annotated
