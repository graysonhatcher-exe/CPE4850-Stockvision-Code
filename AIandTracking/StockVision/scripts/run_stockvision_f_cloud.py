# === Begin Imports ===
import numpy as np
import cv2
from ultralytics import YOLO
import sys
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from ultralytics.trackers.byte_tracker import BYTETracker
from ultralytics.cfg import get_cfg
from ultralytics.utils.checks import check_yaml
# === End Imports ===


# === Configuration Begin ===

# == YOLO Model Import ==
model = YOLO(r"E:\StockVision\weights\best.pt").to('cuda')
imagesize = 480
confidence = 0.5

# == Point of Update ==
EXIT_LINE_Y = 200  # Y-coordinate for entry/exit threshold

# == Camera Feeds Setup ==
cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)

# == ByteTrack Config ==
cfg = get_cfg(check_yaml("bytetrack.yaml"))
tracker = BYTETracker(cfg, frame_rate = 30)

# === Configuration end ===

# === Initializations Begin ===

# == Local Inventory (TEMP) == 
inventory = {
    "Granola Bar": 0,
    "Gummy": 0,
    "Crackers": 0,
    "Doritos": 0,
    "Butter Finger": 0,
    "Canned-Corn": 0,
    "Canned-Peas": 0,
    "Canned-Tuna": 0,
    "Mac-And-Cheese": 0,
    "Ramen": 0
}

# == Object History Cache ==
object_history = {}

# == Camera storages ==
detections_cam1 = []
detections_cam2 = []

# == Firebase Initialization ==
#cred = credentials.Certificate("serviceAccountKey.json")
cred = credentials.Certificate(r"E:\StockVision\test-d1cec-3523c37cf45c.json")
firebase_admin.initialize_app(cred)
db = firestore.client()  # Firestore client instead of Realtime DB
user_id = "EwUldNgNHpeLzLdxhRXBSKllKC82"


# === Configuration End ===


# === Update Cloud Inventory Function ===
def update_inventory(label: str, change: int):
    pantry_ref = db.collection("users").document(user_id).collection("pantry")
    
    # Process item_name to match format of Firestore
    item_name= label.replace("-", " ")

    # Find document where field name == item_name
    query = pantry_ref.where("name", "==", item_name).limit(1).get()

    if not query:
        print(f"No existing item found for '{item_name}' in pantry.")
        return

    doc = query[0]
    doc_ref = doc.reference
    data = doc.to_dict()

    # Parse current quantity, handle units (e.g. "1 LB")
    current_qty_str = str(data.get("quantity", "0"))
    numeric_part = ''.join([c for c in current_qty_str if c.isdigit()])
    unit_part = ''.join([c for c in current_qty_str if not c.isdigit()]).strip() or "unit"

    try:
        current_qty = int(numeric_part)
    except ValueError:
        current_qty = 0

    new_qty = max(current_qty + change, 0)
    new_quantity_str = f"{new_qty} {unit_part}"

    timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    # Update existing document
    doc_ref.update({
        "quantity": new_quantity_str,
        "timestamp": timestamp
    })

    print(f"Updated {item_name}: {current_qty_str} → {new_quantity_str} at {timestamp}")
# === End of Function ===

# === Extract Detections Function == 
def extract_detections(results):
        x1, y1, x2, y2 = box.xyxy[0]
        w = x2 - x1
        h = y2 - y1
        score = float(box.conf[0])
        cls = int(box.cls[0])
        dets.append([x1, y1, w, h, score, cls])
        
        dets_np = np.array(dets, dtype=np.float32)
        tracks_cam1 = tracker.update(dets_np, frame1.shape, frame1)
        
        detections_cam1.append({
            "label": label,
            "conf": conf,
            "bbox": (x1, y1, x2, y2),
            "center": center
        })
    



# ==== MAIN DETECTION LOOP ====
while True:
    
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()
    
    if not ret1 or not ret2:
        break

    # Run YOLO detection
    results1 = model(frame1, imgsz=imagesize, conf=confidence)[0]
    results2 = model(frame2, imgsz=imagesize, conf=confidence)[0]

    # Extract detection results for cam 1
    detections_cam1 = []
    for box in results1.boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        w = x2 - x1
        h = y2 - y1
        score = float(box.conf[0])
        cls = int(box.cls[0])
        dets.append([x1, y1, w, h, score, cls])
        
        dets_np = np.array(dets, dtype=np.float32)
        tracks_cam1 = tracker.update(dets_np, frame1.shape, frame1)
        
        detections_cam1.append({
            "label": label,
            "conf": conf,
            "bbox": (x1, y1, x2, y2),
            "center": center
        })
        
        cv2.rectangle(frame1, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        

    # Extract detections for camera 2
    detections_cam2 = []
    for box in results2.boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        w = x2 - x1
        h = y2 - y1
        score = float(box.conf[0])
        cls = int(box.cls[0])
        dets.append([x1, y1, w, h, score, cls])
        
        dets_np = np.array(dets, dtype=np.float32)
        tracks_cam2 = tracker.update(dets_np, frame2.shape, frame2)

        detections_cam2.append({
            "label": label,
            "conf": conf,
            "bbox": (x1, y1, x2, y2),
            "center": center
        })
        
        cv2.rectangle(frame2, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        
    cv2.imshow("Camera 1", frame1)
    cv2.imshow("Camera 2", frame2)


        if obj_id in object_history:
            prev_y = object_history[obj_id]

            # Item REMOVED (crossed line upward)
            if prev_y > EXIT_LINE_Y and center_y <= EXIT_LINE_Y:
                if inventory.get(label, 0) > 0:
                    inventory[label] -= 1
                    print(f"{label} removed! New count: {inventory[label]}")
                    update_inventory(label, -1)  # Update Firebase

            # Item RETURNED (crossed line downward)
            elif prev_y < EXIT_LINE_Y and center_y >= EXIT_LINE_Y:
                inventory[label] += 1
                print(f"{label} returned! New count: {inventory[label]}")
                update_inventory(label, +1)  # Update Firebase

        # Track last Y position
        object_history[obj_id] = center_y


# === Visualization (NOT NEEDED IN FINAL PRODUCT, ONLY FOR TESTING) ===
        # Draw tracking visuals
        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        cv2.putText(frame, label, (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw the "exit line"
    cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)

    # Show camera feed
    cv2.imshow("StockVision Live", frame)

    # Show inventory window
    inv_img = 255 * np.ones((300, 300, 3), dtype=np.uint8)
    y_offset = 30
    for item, count in inventory.items():
        cv2.putText(inv_img, f"{item}: {count}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        y_offset += 30
    cv2.imshow("Inventory Counts", inv_img)

    # Quit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
