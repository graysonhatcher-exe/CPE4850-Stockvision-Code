# === Begin Imports ===
import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import torch
from collections import deque
# === End Imports ===

# === Configuration ===
CAMERA_SOURCES = [0, 1]  # Indices for cameras
YOLO_MODEL_PATH = r"E:\StockVision\weights\best.pt"
FRAME_WIDTH = 720
FRAME_HEIGHT = 720
CONFIDENCE_THRESHOLD = 0.5
MAX_BUFFER_SIZE = 2  # Keep tiny buffer to avoid lag
FUSION_DISTANCE = 50  # Pixels; objects closer than this are fused across cameras

# Zone definitions (Y coordinates)
INCREMENT_ZONE_Y = 200   # Top of increment zone
DECREMENT_ZONE_Y = 400   # Bottom of decrement zone

# === Camera Zones Configuration ===
# Define each camera's increment/decrement proportions
camera_zones = [
    {"inc_percent": 0.3, "dec_percent": 0.7},  # Camera 0
    {"inc_percent": 0.25, "dec_percent": 0.75} # Camera 1
]

# Precompute Y coordinates for zones
for zones in camera_zones:
    zones["INCREMENT_ZONE_Y"] = int(FRAME_HEIGHT * zones["inc_percent"])
    zones["DECREMENT_ZONE_Y"] = int(FRAME_HEIGHT * zones["dec_percent"])
    
# === End Configuration ===

# === Firebase Setup ===
cred = credentials.Certificate(r"E:\StockVision\test-d1cec-3523c37cf45c.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
USER_ID = "EwUldNgNHpeLzLdxhRXBSKllKC82"
pantry_ref = db.collection("users").document(USER_ID).collection("pantry")
# === End Firebase Setup ===

# === Load YOLO Model on GPU ===
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
model = YOLO(YOLO_MODEL_PATH)
model.to(device)
# === End Model Setup ===

# === Camera Initialization ===
caps = [cv2.VideoCapture(src) for src in CAMERA_SOURCES]
for cap in caps:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 60)
# === End Camera Setup ===

# === Local Inventory Cache ===
inventory = {}
# === End Inventory ===

# === Object History for Tracking & Fusion ===
object_history = {}
# === End History ===

# === Frame Buffers (one per camera) ===
frame_buffers = {i: deque(maxlen=MAX_BUFFER_SIZE) for i in range(len(CAMERA_SOURCES))}
# === End Frame Buffers ===

# === Firebase Update Function (unchanged) ===
def update_inventory(label: str, change: int):
    query = pantry_ref.where("name", "==", label.replace("-", " ")).limit(1).get()
    if not query:
        print(f"No pantry item found for '{label}'")
        return
    doc_ref = query[0].reference
    data = query[0].to_dict()
    current_qty_str = str(data.get("quantity", "0"))
    numeric_part = ''.join(c for c in current_qty_str if c.isdigit())
    unit_part = ''.join(c for c in current_qty_str if not c.isdigit()).strip() or "unit"
    try:
        current_qty = int(numeric_part)
    except ValueError:
        current_qty = 0
    new_qty = max(current_qty + change, 0)
    new_quantity_str = f"{new_qty} {unit_part}"
    timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    doc_ref.update({"quantity": new_quantity_str, "timestamp": timestamp})
    print(f"[{datetime.now()}] Updated {label}: {current_qty_str} → {new_quantity_str}")
# === End Firebase Function ===

# === Helper: determine zone based on center_y ===
def get_zone(center_y, increment_y, decrement_y):
    if center_y <= increment_y:
        return "increment"
    elif center_y >= decrement_y:
        return "decrement"
    else:
        return None
# === End Helper ===

# === Main Detection Loop ===
try:
    while True:
        # Capture frames for all cameras
        for cam_index, cap in enumerate(caps):
            ret, frame = cap.read()
            if not ret:
                print(f"Camera {cam_index} failed to read frame.")
                continue
            frame_buffers[cam_index].append(frame)

        # Process only latest frame per camera
        for cam_index, buffer in frame_buffers.items():
            if not buffer:
                continue
            frame = buffer.pop()   # Latest frame
            buffer.clear()         # Drop old frames to avoid backlog
            
            zones = camera_zones[cam_index]  # get this camera's zones
            increment_y = zones["INCREMENT_ZONE_Y"]
            decrement_y = zones["DECREMENT_ZONE_Y"]

            # Run YOLO
            results = model(frame, imgsz=FRAME_WIDTH, conf=CONFIDENCE_THRESHOLD)[0]

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                x1, y1, x2, y2 = box.xyxy[0]
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                confidence = float(box.conf[0])

                # --- Multi-camera fusion ---
                fused_id = None
                for obj_id, data in object_history.items():
                    if label in obj_id:
                        prev_x, prev_y = data["center"]
                        if abs(center_x - prev_x) < FUSION_DISTANCE and abs(center_y - prev_y) < FUSION_DISTANCE:
                            fused_id = obj_id
                            if confidence > data.get("confidence", 0):
                                data["confidence"] = confidence
                            break

                if fused_id is None:
                    fused_id = f"Cam{cam_index}_{label}_{center_x}_{center_y}"
                    current_zone = get_zone(center_y, increment_y, decrement_y)
                    object_history[fused_id] = {
                        "center": (center_x, center_y),
                        "confidence": confidence,
                        "last_seen": datetime.now(),
                        "last_zone": current_zone
                    }
                    continue  # First appearance: establish presence, no inventory change

                # --- Zone-based inventory logic ---
                current_zone = get_zone(center_y, increment_y, decrement_y)
                last_zone = object_history[fused_id]["last_zone"]

                if last_zone == "increment" and current_zone == "decrement":
                    # Decrement inventory
                    if label not in inventory:
                        inventory[label] = 0
                    inventory[label] = max(inventory.get(label,0) - 1, 0)
                    update_inventory(label, -1)
                    print(f"[{datetime.now()}] {label} decremented!")

                elif last_zone == "decrement" and current_zone == "increment":
                    # Increment inventory
                    if label not in inventory:
                        inventory[label] = 0
                    inventory[label] += 1
                    update_inventory(label, +1)
                    print(f"[{datetime.now()}] {label} incremented!")

                # --- Update object history ---
                object_history[fused_id]["center"] = (center_x, center_y)
                object_history[fused_id]["last_seen"] = datetime.now()
                object_history[fused_id]["last_zone"] = current_zone
                object_history[fused_id]["confidence"] = confidence
                
        # Remove old objects from history
        TIMEOUT_SECONDS = 5  # Tune as needed
        now = datetime.now()
        to_delete = []
        for obj_id, data in object_history.items():
            if (now - data["last_seen"]).total_seconds() > TIMEOUT_SECONDS:
                to_delete.append(obj_id)
        for obj_id in to_delete:
            del object_history[obj_id]

except KeyboardInterrupt:
    print("Exiting...")

finally:
    for cap in caps:
        cap.release()
