# views.py
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings

import os, time, cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO
from .sort.sort import Sort
from .util import get_car, read_license_plate, write_csv

# CURRENT_DIR = Path(__file__).resolve().parent
# MODEL_PATH = CURRENT_DIR / 'license_plate_detector.pt'
# COCO_MODEL_PATH = CURRENT_DIR / 'models/yolov8n.pt'

# Globals
capture_active = False
results = {}
frame_data = {}
frame_nmr = -1
mot_tracker = Sort()
coco_model = YOLO("./models/yolov8n.pt")
license_plate_detector = YOLO("./models/license_plate_detector.pt")
vehicles = [2, 3, 5, 7]

uploaded_video_path = None

def is_core_user(user):
    return user.is_authenticated and user.role in ['core', 'admin']


class VideoCamera:
    def __init__(self, source=0):
        self.video = cv2.VideoCapture(source)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        global frame_nmr, results
        frame_nmr += 1
        ret, frame = self.video.read()
        if not ret:
            return None

        results[frame_nmr] = {}
        detections = coco_model(frame)[0]
        detections_ = []

        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        track_ids = mot_tracker.update(np.asarray(detections_))
        license_plates = license_plate_detector(frame)[0]
        vehicle_data = []

        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
            if car_id != -1:
                license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 64, 255, cv2.THRESH_BINARY_INV)
                license_text, license_score = read_license_plate(thresh)

                if license_text:
                    results[frame_nmr][car_id] = {
                        'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                        'license_plate': {
                            'bbox': [x1, y1, x2, y2],
                            'text': license_text,
                            'bbox_score': score,
                            'text_score': license_score
                        }
                    }
                    vehicle_data.append({'id': car_id, 'text': license_text})
                    cv2.putText(frame, license_text, (int(x1), int(y1)-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        frame_data[frame_nmr] = vehicle_data
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()


def gen(camera):
    global capture_active
    capture_active = True
    while capture_active:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break
        time.sleep(0.05)


@login_required
@user_passes_test(is_core_user)
def dashboard(request):
    return render(request, 'vehicle_monitoring/dashboard.html')


@login_required
@user_passes_test(is_core_user)
def video_feed(request):
    global uploaded_video_path
    source = request.GET.get('source', 'webcam')

    if source == 'file' and uploaded_video_path:
        return StreamingHttpResponse(
            gen(VideoCamera(uploaded_video_path)),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    else:
        return StreamingHttpResponse(
            gen(VideoCamera(0)),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )


@login_required
@user_passes_test(is_core_user)
def stop_stream(request):
    global capture_active
    capture_active = False
    write_csv(results, os.path.join(settings.MEDIA_ROOT, 'vehicle_results.csv'))
    return JsonResponse({'status': 'stopped'})


@login_required
@user_passes_test(is_core_user)
def fetch_vehicle_data(request):
    if not capture_active:
        return JsonResponse({'data': []})
    if frame_data:
        latest = max(frame_data.keys())
        return JsonResponse({'data': frame_data[latest]})
    return JsonResponse({'data': []})


@csrf_exempt
@login_required
@user_passes_test(is_core_user)
def upload_file(request):
    global uploaded_video_path
    if request.method == 'POST' and request.FILES.get('video_file'):
        video = request.FILES['video_file']
        media_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_video.mp4')
        with open(media_path, 'wb+') as f:
            for chunk in video.chunks():
                f.write(chunk)
        uploaded_video_path = media_path
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'})
