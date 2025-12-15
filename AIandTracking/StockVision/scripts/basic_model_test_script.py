import numpy as np
import cv2
from ultralytics import YOLO

model = YOLO(r"C:\Users\Grayson\runs\detect\exp_10_classes_2\weights\best.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=720, conf=0.5)[0]

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        x1, y1, x2, y2 = box.xyxy[0]
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        obj_id = f"{label}_{round(center_x, -2)}"

        # Draw center dot and label
        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        cv2.putText(frame, label, (int(x1), int(y1)-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Show Camera Feed
    cv2.imshow("StockVision Live", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()