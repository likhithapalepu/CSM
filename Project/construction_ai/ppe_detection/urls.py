from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='ppe_dashboard'),
    path('video_feed/', views.video_feed, name='ppe_video_feed'),
    path('start_stream/', views.start_stream, name='ppe_start_stream'),
    path('start_file/', views.start_file, name='ppe_start_file'),
    path('stop_stream/', views.stop_stream, name='ppe_stop_stream'),
    path('download_results/', views.download_results, name='ppe_download_results'),
]
