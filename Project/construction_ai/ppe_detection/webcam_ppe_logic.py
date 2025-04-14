# ppe_detection/webcam_ppe_logic.py
import cv2
import time
from ultralytics import YOLO
from .webcam import draw_text_with_background

model = YOLO("./models/ppe.pt")

def process_video_stream(source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        hardhat_count = 0
        vest_count = 0
        person_count = 0

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                cls = int(box.cls[0])
                label = f"{model.names[cls]} ({confidence:.2f})"

                if model.names[cls] == "Hardhat":
                    hardhat_count += 1
                elif model.names[cls] == "Safety Vest":
                    vest_count += 1
                elif model.names[cls] == "Person":
                    person_count += 1

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                draw_text_with_background(frame, label, (x1, y1 - 10))

        _, jpeg = cv2.imencode('.jpg', cv2.resize(frame, (640, 480)))
        yield jpeg.tobytes(), {'hardhats': hardhat_count, 'vests': vest_count, 'people': person_count}

    cap.release()
