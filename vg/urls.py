from django.urls import path

from .views import manometer, get_manometer_records, submit_test_beginning, submit_test_end, database_health_check

app_name = "vg"

urlpatterns = [
    path("manometr", manometer, name='manometer'),
    path("get_manometer_records", get_manometer_records, name='get_manometer_records'),
    path("submit_test_beginning", submit_test_beginning, name='submit_test_beginning'),
    path("submit_test_end", submit_test_end, name='submit_test_end'),
    path("database_health_check", database_health_check, name='database_health_check'),
]