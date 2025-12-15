import numpy as np
import cv2
from ultralytics import YOLO
import sys
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# === Configuration Begin ===

# == YOLO Model ==
# Ensure this path is correct
model = YOLO("/home/vision_da_best/Desktop/StockVision/best.pt") 
imagesize = 480 
confidence = 0.5 

# == Point of Update ==
EXIT_LINE_Y = 200  

# == Camera Feed Input ==
# We put cameras in a list. 
# Use 0 and 1 for USB webcams, or file paths for video files.
sources = [
    0, # Camera 1 (Index 0)
    1  # Camera 2 (Index 1) - If this fails, change to a video path for testing
]

# Initialize VideoCapture objects
caps = [cv2.VideoCapture(src) for src in sources]

# == Local Inventory (TEMP) == 
inventory = {
    "Canned-Corn": 1,
    "Canned-Peas": 2,
}

# == Object History Cache ==
object_history = {}

# == Firebase Initialization ==
try:
    cred = credentials.Certificate("/home/vision_da_best/Desktop/StockVision/test-d1cec-3523c37cf45c.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    user_id = "JwiDjltQjtUn1NFsXUJ1JsWYCt03"
    print("Firebase Connected.")
except Exception as e:
    print(f"Firebase Error (ignored for local testing): {e}")
    db = None # Handle cases where DB fails so script keeps running

# === Update Cloud Inventory Function ===
def update_inventory(label: str, change: int):
    if db is None: return # Skip if DB isn't connected

    pantry_ref = db.collection("users").document(user_id).collection("pantry")
    item_name = label.replace("-", " ")
    query = pantry_ref.where("name", "==", item_name).limit(1).get()

    if not query:
        print(f"No existing item found for '{item_name}' in pantry.")
        return

    doc = query[0]
    doc_ref = doc.reference
    data = doc.to_dict()

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

    doc_ref.update({
        "quantity": new_quantity_str,
        "timestamp": timestamp
    })
    print(f"Updated {item_name}: {current_qty_str} -> {new_quantity_str}")

# ==== MAIN DETECTION LOOP ====
while True:
    frames_to_display = []

    # Loop through every camera provided in 'caps'
    for cam_index, cap in enumerate(caps):
        ret, frame = cap.read()
        
        if not ret:
            print(f"Failed to read from Camera {cam_index}")
            continue # Skip this camera for this iteration

        # Run YOLO detection on current frame
        results = model(frame, imgsz=imagesize, conf=confidence, verbose=False)[0]
        
        # Process each detected object
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            x1, y1, x2, y2 = box.xyxy[0]
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # === CRITICAL CHANGE ===
            # We must add the cam_index to the ID.
            # Otherwise, an object at x=100 on Cam1 looks like an object at x=100 on Cam2.
            obj_id = f"Cam{cam_index}_{label}_{round(center_x, -2)}"

            if obj_id in object_history:
                prev_y = object_history[obj_id]

                # Item REMOVED (crossed line upward)
                if prev_y > EXIT_LINE_Y and center_y <= EXIT_LINE_Y:
                    if inventory.get(label, 0) > 0:
                        inventory[label] -= 1
                        print(f"CAM {cam_index}: {label} removed!")
                        update_inventory(label, -1)

                # Item RETURNED (crossed line downward)
                elif prev_y < EXIT_LINE_Y and center_y >= EXIT_LINE_Y:
                    inventory[label] += 1
                    print(f"CAM {cam_index}: {label} returned!")
                    update_inventory(label, +1)

            # Update history
            object_history[obj_id] = center_y

            # Draw tracking visuals on the frame
            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"{label} {confidence:.2f}", (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw the "exit line"
        cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)
        
        # Label the camera ID on screen
        cv2.putText(frame, f"CAM {cam_index}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
        
        # Resize for display consistency
        frame_resized = cv2.resize(frame, (640, 480))
        frames_to_display.append(frame_resized)

    # === Display Logic ===
    if frames_to_display:
        # Stack frames horizontally (side-by-side)
        combined_view = np.hstack(frames_to_display)
        cv2.imshow("StockVision Multi-Cam", combined_view)
    
    # Show inventory window (Same as before)
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

# Release all cameras
for cap in caps:
    cap.release()
cv2.destroyAllWindows()