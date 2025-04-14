import cv2
import os
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from .stream import VideoCamera

video_camera = None
is_streaming = False
video_source = None
results_summary = {}

def dashboard(request):
    global video_source, results_summary
    return render(request, 'ppe_detection/dashboard.html', {
        'video_source': video_source,
        'results': results_summary,
    })

def video_feed(request):
    return StreamingHttpResponse(video_camera.generate(), content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def start_stream(request):
    global video_camera, is_streaming, video_source
    if request.method == 'POST':
        video_camera = VideoCamera(source=0)
        is_streaming = True
        video_source = 'webcam'
    return redirect('ppe_dashboard')

@csrf_exempt
def start_file(request):
    global video_camera, is_streaming, video_source
    if request.method == 'POST' and request.FILES.get('video_file'):
        video_file = request.FILES['video_file']
        path = f'media/{video_file.name}'
        with open(path, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        video_camera = VideoCamera(source=path)
        is_streaming = True
        video_source = 'file'
    return redirect('ppe_dashboard')

@csrf_exempt
def stop_stream(request):
    global is_streaming, video_camera, results_summary
    if request.method == 'POST' and video_camera:
        is_streaming = False
        results_summary = video_camera.get_summary()
        video_camera.release()
    return redirect('ppe_dashboard')

def download_results(request):
    filepath = 'media/ppe_results.csv'
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True)
    else:
        return redirect('ppe_dashboard')
