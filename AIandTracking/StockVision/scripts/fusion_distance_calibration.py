import cv2
import numpy as np
from ultralytics import YOLO
import torch
from datetime import datetime

# === Configuration ===
CAMERA_SOURCES = [0, 1]         # Camera indices
YOLO_MODEL_PATH = r"E:\StockVision\weights\best.pt"
FRAME_WIDTH = 720
FRAME_HEIGHT = 720
CONFIDENCE_THRESHOLD = 0.5
FUSION_DISTANCE = 50            # Pixels, adjust for testing

# === Load YOLO on GPU ===
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
model = YOLO(YOLO_MODEL_PATH)
model.to(device)

# === Initialize cameras ===
caps = [cv2.VideoCapture(src) for src in CAMERA_SOURCES]
for cap in caps:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 60)

# === Object history for fusion ===
object_history = {}  # fused_id -> center

try:
    while True:
        frames = []
        detections = []

        # Capture frames from all cameras
        for cam_index, cap in enumerate(caps):
            ret, frame = cap.read()
            if not ret:
                print(f"Camera {cam_index} failed")
                continue
            frames.append(frame)

            # YOLO detection
            results = model(frame, imgsz=FRAME_WIDTH, conf=CONFIDENCE_THRESHOLD)[0]

            cam_detections = []
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                x1, y1, x2, y2 = box.xyxy[0]
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                confidence = float(box.conf[0])
                cam_detections.append({
                    "label": label,
                    "center": (center_x, center_y),
                    "cam_index": cam_index,
                    "confidence": confidence
                })
            detections.append(cam_detections)

        # --- Fusion logic ---
        fused_objects = {}
        for cam_detections in detections:
            for det in cam_detections:
                label = det["label"]
                center_x, center_y = det["center"]
                cam_index = det["cam_index"]
                confidence = det["confidence"]

                fused_id = None
                # Compare with existing objects
                for obj_id, obj_data in object_history.items():
                    if label in obj_id:
                        prev_x, prev_y = obj_data["center"]
                        dx = abs(center_x - prev_x)
                        dy = abs(center_y - prev_y)
                        distance = np.sqrt(dx**2 + dy**2)
                        if distance < FUSION_DISTANCE:
                            fused_id = obj_id
                            print(f"[{datetime.now()}] FUSED {label} from Cam{cam_index} with {obj_id}, distance={distance:.1f}")
                            break

                if fused_id is None:
                    fused_id = f"Cam{cam_index}_{label}_{center_x}_{center_y}"
                    print(f"[{datetime.now()}] NEW object: {fused_id}")

                fused_objects[fused_id] = {"center": (center_x, center_y)}

        # Update object history
        object_history = fused_objects

        # --- Visualization ---
        if frames:
            combined = np.hstack([cv2.resize(f, (FRAME_WIDTH, FRAME_HEIGHT)) for f in frames])
            for obj_id, data in object_history.items():
                x, y = data["center"]
                cv2.circle(combined, (x + 0 if len(frames) == 1 else x + FRAME_WIDTH*0, y), 10, (0,255,0), -1)
                cv2.putText(combined, obj_id, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv2.imshow("Fusion Test", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Exiting...")

finally:
    for cap in caps:
        cap.release()
    cv2.destroyAllWindows()
