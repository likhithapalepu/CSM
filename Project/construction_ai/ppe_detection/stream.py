import cv2
import time
from ultralytics import YOLO

class VideoCamera:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        self.model = YOLO("./models/ppe.pt")
        self.person_count = 0
        self.hardhat_count = 0
        self.vest_count = 0

    def __del__(self):
        self.release()

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def get_summary(self):
        return {
            'person': self.person_count,
            'hardhat': self.hardhat_count,
            'vest': self.vest_count,
        }

    def generate(self):
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                break

            results = self.model(frame)
            people = 0
            hardhats = 0
            vests = 0

            for result in results:
                if result.boxes:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        label = self.model.names[cls]

                        if label == "Person":
                            people += 1
                        elif label == "Hardhat":
                            hardhats += 1
                        elif label == "Safety Vest":
                            vests += 1

                        color = (0, 255, 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            self.person_count += people
            self.hardhat_count += hardhats
            self.vest_count += vests

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            time.sleep(0.03)
