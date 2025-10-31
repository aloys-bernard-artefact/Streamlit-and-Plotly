from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pages/data-exploration', views.data_exploration, name='data_exploration'),
    path('pages/time-series', views.time_series, name='time_series'),
    path('pages/time-series/download', views.download_csv, name='download_csv'),
]
