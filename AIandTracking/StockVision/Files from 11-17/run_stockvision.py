import numpy as np
import cv2
from ultralytics import YOLO

# ==== CONFIG ====
EXIT_LINE_Y = 200  # Y-coordinate for entry/exit threshold
inventory = {"Granola Bar": 0, "Gummy": 0, "Crackers": 0, "Doritos": 0, "Butter Finger": 0, "Canned-Corn": 0, "Canned-Peas": 0, "Canned-Tuna": 0, "Mac-And-Cheese": 0, "Ramen": 0}

model = YOLO("/home/vision_da_best/Desktop/StockVision/best.pt") #Model Filepath
cap = cv2.VideoCapture(0)

object_history = {}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=480, conf=0.5)[0]

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        x1, y1, x2, y2 = box.xyxy[0]
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        obj_id = f"{label}_{round(center_x, -2)}"

        if obj_id in object_history:
            prev_y = object_history[obj_id]

            # Moved UP past the line (removed)
            if prev_y > EXIT_LINE_Y and center_y <= EXIT_LINE_Y:
                if inventory.get(label, 0) > 0:
                    inventory[label] -= 1
                    print(f"{label} removed! New count: {inventory[label]}")
            # Moved DOWN past the line (returned)
            elif prev_y < EXIT_LINE_Y and center_y >= EXIT_LINE_Y:
                inventory[label] += 1
                print(f"{label} returned! New count: {inventory[label]}")

        object_history[obj_id] = center_y

        # Draw center dot and label
        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        cv2.putText(frame, label, (int(x1), int(y1)-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw Exit Line
    cv2.line(frame, (0, EXIT_LINE_Y), (frame.shape[1], EXIT_LINE_Y), (0, 0, 255), 2)

    # Show Camera Feed
    cv2.imshow("StockVision Live", frame)

    # Show Inventory in Separate Window
    inv_img = 255 * np.ones((300, 300, 3), dtype=np.uint8)
    y_offset = 30
    for item, count in inventory.items():
        cv2.putText(inv_img, f"{item}: {count}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        y_offset += 30
    cv2.imshow("Inventory Counts", inv_img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
