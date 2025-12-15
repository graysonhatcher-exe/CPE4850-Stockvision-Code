import cv2
import numpy as np
from ultralytics import YOLO
import torch
from datetime import datetime

# === Configuration ===
CAMERA_INDEX = 0              # Single camera for testing
YOLO_MODEL_PATH = r"E:\StockVision\weights\best.pt"
FRAME_WIDTH = 720
FRAME_HEIGHT = 720
CONFIDENCE_THRESHOLD = 0.5

# Zone proportions (percent of frame height)
INC_PERCENT = 0.3             # 30% top = increment zone
DEC_PERCENT = 0.7             # 70% bottom = decrement zone
# Automatically calculated:
INCREMENT_ZONE_Y = int(FRAME_HEIGHT * INC_PERCENT)
DECREMENT_ZONE_Y = int(FRAME_HEIGHT * DEC_PERCENT)

# === Load YOLO on GPU ===
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
model = YOLO(YOLO_MODEL_PATH)
model.to(device)

# === Initialize camera ===
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 60)

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

# === Object history ===
object_history = {}

# === Helper function: determine zone ===
def get_zone(center_y):
    if center_y <= INCREMENT_ZONE_Y:
        return "increment"
    elif center_y >= DECREMENT_ZONE_Y:
        return "decrement"
    else:
        return None

# === Main Loop ===
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # YOLO detection
        results = model(frame, imgsz=FRAME_WIDTH, conf=CONFIDENCE_THRESHOLD)[0]
        
        for cam_index, cap in enumerate(caps):
            ret, frame = cap.read()
            if not ret:
            continue

        zones = camera_zones[cam_index]  # get this camera's zones
        increment_y = zones["INCREMENT_ZONE_Y"]
        decrement_y = zones["DECREMENT_ZONE_Y"]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            x1, y1, x2, y2 = box.xyxy[0]
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # Use position-based ID
            obj_id = f"{label}_{round(center_x, -2)}"

            current_zone = get_zone(center_y)
            last_zone = object_history.get(obj_id, None)

            # --- Zone transition logic ---
            if last_zone == "increment" and current_zone == "decrement":
                print(f"[{datetime.now()}] {label} Decremented")
            elif last_zone == "decrement" and current_zone == "increment":
                print(f"[{datetime.now()}] {label} Incremented")

            # Update object history
            if current_zone is not None:
                object_history[obj_id] = current_zone

        # --- Visualization for calibration ---
        vis_frame = frame.copy()
        cv2.line(vis_frame, (0, INCREMENT_ZONE_Y), (FRAME_WIDTH, INCREMENT_ZONE_Y), (0, 255, 0), 2)
        cv2.putText(vis_frame, "Increment Zone", (10, INCREMENT_ZONE_Y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        cv2.line(vis_frame, (0, DECREMENT_ZONE_Y), (FRAME_WIDTH, DECREMENT_ZONE_Y), (0, 0, 255), 2)
        cv2.putText(vis_frame, "Decrement Zone", (10, DECREMENT_ZONE_Y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        # Draw object centers
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            cv2.circle(vis_frame, (center_x, center_y), 5, (255,255,0), -1)

        cv2.imshow("Zone Calibration", vis_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Exiting...")

finally:
    cap.release()
    cv2.destroyAllWindows()
