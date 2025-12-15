# === Begin Imports ===
import numpy as np
import cv2
from ultralytics import YOLO
import sys
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
# === End Imports ===


# === Configuration Begin ===

# == YOLO Model Import and Configuration ==
model = YOLO("/home/vision_da_best/Desktop/StockVision/best.pt") #Model Filepath
imagesize = 480 #Input image size
confidence = 0.5 #Confidence Threshold

# == Point of Update ==
EXIT_LINE_Y = 200  # Y-coordinate for entry/exit threshold

# == Camera Feed Input ==
cap = cv2.VideoCapture(0)

# === Configuration end ===

# === Initializations Begin ===

# == Local Inventory (TEMP) == 
inventory = {
    "Canned-Corn": 1,
    "Canned-Peas": 2,
}

# == Object History Cache ==
object_history = {}

# == Firebase Initialization and Config ==
#cred = credentials.Certificate("serviceAccountKey.json")
cred = credentials.Certificate("/home/vision_da_best/Desktop/StockVision/test-d1cec-3523c37cf45c.json") #Credentials Filepath
firebase_admin.initialize_app(cred)
db = firestore.client()  # Firestore client instead of Realtime DB
user_id = "JwiDjltQjtUn1NFsXUJ1JsWYCt03"


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



# ==== MAIN DETECTION LOOP ====
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO detection
    results = model(frame, imgsz=imagesize, conf=confidence)[0]

    # Process each detected object
    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        x1, y1, x2, y2 = box.xyxy[0]
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        obj_id = f"{label}_{round(center_x, -2)}"

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
