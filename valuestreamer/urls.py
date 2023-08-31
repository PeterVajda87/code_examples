from django.urls import path

from .views import transfer, transfer_from_csv

app_name = "valuestreamer"

urlpatterns = [
    path("", transfer, name='transfer'),
    path("csv", transfer_from_csv, name='transfer_from_csv'),
]