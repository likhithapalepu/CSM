from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='vehicle_dashboard'),
    path('video-feed/', views.video_feed, name='vehicle_video_feed'),
    path('stop/', views.stop_stream, name='vehicle_stop'),
    path('upload/', views.upload_file, name='vehicle_upload_file'),
    path('data/', views.fetch_vehicle_data, name='vehicle_data'),
]

