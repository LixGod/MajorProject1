import os
import json
import asyncio
import time
import base64
from typing import Dict, List, Any, Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.junction.junction_config import JunctionConfig, ApproachConfig, ControlParams, LocationConfig
from src.control.junction_runtime import JunctionRuntime
from src.map.junction_geocoder import JunctionGeocoder
from src.evaluation.signal_control_benchmark import SignalControlBenchmark
from src.perception.types import Detection, Frame
from src.perception.detector import DetectorEngine

app = FastAPI(
    title="Smart Traffic Signal Control System API",
    description="Adaptive Multi-Junction Max-Pressure Signal Control & Real-Time Visualization Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

geocoder = JunctionGeocoder()
junction_runtimes: Dict[str, JunctionRuntime] = {}
junction_locations: Dict[str, Any] = {}
detector_engine = DetectorEngine({"perception": {"confidence_threshold": 0.35}})

class OverrideRequest(BaseModel):
    phase_id: int
    operator_id: str = "operator_1"
    reason: str = "Manual override"

class TomTomSearchRequest(BaseModel):
    query: str

class AddJunctionRequest(BaseModel):
    junction_id: str
    name: str
    num_approaches: int = 4

def initialize_mumbai_junctions():
    mumbai_junctions_def = [
        {
            "id": "weh_vile_parle",
            "name": "WEH Vile Parle Junction",
            "approaches": ["north", "south", "east", "west"]
        },
        {
            "id": "bkc_connector",
            "name": "Bandra Kurla Complex Junction",
            "approaches": ["north", "south", "east"]
        },
        {
            "id": "dadar_tt_circle",
            "name": "Dadar TT Circle",
            "approaches": ["north", "south", "east", "west"]
        },
        {
            "id": "andheri_flyover",
            "name": "Andheri SV Road Junction",
            "approaches": ["north", "south", "east", "west"]
        },
        {
            "id": "powai_galleria",
            "name": "Powai Hiranandani Junction",
            "approaches": ["north", "south", "east"]
        }
    ]

    for jdef in mumbai_junctions_def:
        app_configs = [
            ApproachConfig(
                id=app_id,
                lanes=3,
                camera_source="synthetic",
                movements=["through", "left", "right"] if len(jdef["approaches"]) == 4 else ["through", "left"],
                downstream_link_id=f"link_{app_id}"
            ) for app_id in jdef["approaches"]
        ]
        cfg = JunctionConfig(
            junction_id=jdef["id"],
            name=jdef["name"],
            num_approaches=len(jdef["approaches"]),
            approaches=app_configs
        )
        rt = JunctionRuntime(cfg)
        junction_runtimes[cfg.junction_id] = rt

        loc = geocoder.resolve_junction_location(cfg.junction_id, cfg.name)
        junction_locations[cfg.junction_id] = loc.model_dump()

initialize_mumbai_junctions()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def start_background_control_loop():
    async def loop():
        tick_count = 0
        while True:
            await asyncio.sleep(1.0)
            tick_count += 1
            combined_telemetry = {}

            for j_id, rt in junction_runtimes.items():
                mock_dets: Dict[str, List[Detection]] = {}
                for app_config in rt.config.approaches:
                    app_id = app_config.id
                    q_sim = max(0, int((tick_count * 0.7 + hash(app_id)) % 8))
                    dets = []
                    for i in range(q_sim):
                        dets.append(
                            Detection(
                                track_id=100 + i,
                                class_id=4,
                                class_name="car",
                                confidence=0.92,
                                bbox=(10.0, 10.0, 50.0, 50.0)
                            )
                        )
                    if j_id == "weh_vile_parle" and app_id == "north" and (tick_count % 45 in [15, 16, 17]):
                        dets.append(
                            Detection(
                                track_id=999,
                                class_id=7,
                                class_name="ambulance",
                                confidence=0.98,
                                bbox=(20.0, 20.0, 80.0, 80.0)
                            )
                        )
                    mock_dets[app_id] = dets

                telem = await rt.tick(mock_dets, dt_sec=1.0)
                telem["location"] = junction_locations.get(j_id, {})
                combined_telemetry[j_id] = telem

            await manager.broadcast({
                "type": "TELEMETRY_UPDATE",
                "timestamp": time.time(),
                "junctions": combined_telemetry
            })

    asyncio.create_task(loop())

# REST API Endpoints
@app.get("/api/junctions")
def list_junctions():
    result = []
    for j_id, rt in junction_runtimes.items():
        result.append({
            "junction_id": j_id,
            "name": rt.config.name,
            "num_approaches": rt.config.num_approaches,
            "location": junction_locations.get(j_id, {}),
            "phases": [p.model_dump() for p in rt.phases]
        })
    return result

@app.get("/api/junctions/{junction_id}")
def get_junction(junction_id: str):
    if junction_id not in junction_runtimes:
        raise HTTPException(status_code=404, detail="Junction not found")
    rt = junction_runtimes[junction_id]
    return {
        "config": rt.config.model_dump(),
        "location": junction_locations.get(junction_id, {}),
        "phases": [p.model_dump() for p in rt.phases],
        "audit_logs": rt.audit_logs
    }

@app.post("/api/junctions/{junction_id}/override")
def apply_override(junction_id: str, req: OverrideRequest):
    if junction_id not in junction_runtimes:
        raise HTTPException(status_code=404, detail="Junction not found")
    rt = junction_runtimes[junction_id]
    rt.set_manual_override(req.phase_id, req.operator_id, req.reason)
    return {"status": "success", "message": f"Manual override applied for Phase {req.phase_id}"}

@app.post("/api/junctions/{junction_id}/clear_override")
def clear_override(junction_id: str):
    if junction_id not in junction_runtimes:
        raise HTTPException(status_code=404, detail="Junction not found")
    rt = junction_runtimes[junction_id]
    rt.clear_manual_override()
    return {"status": "success", "message": "Manual override cleared. Resumed automatic Max-Pressure control."}

@app.post("/api/junctions/search_tomtom")
def search_tomtom(req: TomTomSearchRequest):
    """Searches TomTom Maps API for any junction location in Mumbai."""
    res = geocoder.resolve_junction_location("custom_search", req.query)
    return res.model_dump()

@app.post("/api/junctions/add")
def add_custom_junction(req: AddJunctionRequest):
    """Dynamically geocodes and adds a new Mumbai junction to the active network."""
    loc = geocoder.resolve_junction_location(req.junction_id, req.name)
    app_configs = [
        ApproachConfig(id=aid, lanes=3, camera_source="synthetic", movements=["through", "left", "right"])
        for aid in ["north", "south", "east", "west"][:req.num_approaches]
    ]
    cfg = JunctionConfig(
        junction_id=req.junction_id,
        name=req.name,
        num_approaches=req.num_approaches,
        approaches=app_configs
    )
    rt = JunctionRuntime(cfg)
    junction_runtimes[cfg.junction_id] = rt
    junction_locations[cfg.junction_id] = loc.model_dump()
    return {"status": "success", "location": loc.model_dump()}

@app.post("/api/detect_image")
async def detect_uploaded_image(
    file: UploadFile = File(...),
    model: str = Form("best.pt")
):
    """
    Inference endpoint for user-uploaded traffic images.
    Consumes 'best.pt' or 'local.pt' model weights.
    Returns annotated image (base64) + detected vehicle breakdown.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_np is None:
            raise HTTPException(status_code=400, detail="Invalid image file format")

        h, w = img_np.shape[:2]
        frame = Frame(image=img_np, timestamp=time.time(), camera_id="uploaded_user_image", width=w, height=h)

        detections = await detector_engine.detect_frame(frame, model_choice=model)
        annotated_img = detector_engine.draw_annotations(img_np, detections)

        _, buffer = cv2.imencode('.jpg', annotated_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        category_counts: Dict[str, int] = {}
        for d in detections:
            cname = d.class_name
            category_counts[cname] = category_counts.get(cname, 0) + 1

        return {
            "status": "success",
            "model_used": model,
            "total_vehicles_detected": len(detections),
            "category_counts": category_counts,
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": round(d.confidence, 3),
                    "bbox": d.bbox
                } for d in detections
            ],
            "annotated_image_base64": f"data:image/jpeg;base64,{img_base64}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image detection processing failed: {str(e)}")

@app.get("/api/analytics")
def get_analytics():
    benchmark = SignalControlBenchmark(simulation_ticks=3600)
    comparison = benchmark.run_comparison()
    return comparison

@app.websocket("/ws/junctions")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
