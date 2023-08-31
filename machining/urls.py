from django.urls import URLPattern, path

from .views import machining_view, machining_export, downtimes_entry, visualizations, report

app_name = "machining"

urlpatterns = [
    path("machining_2/", machining_view, name='machining'),
    path("machining/visualizations", visualizations, name='visualizations'),
    path("machining/report/<str:date_from>/<str:date_to>", report, name='report'),
    path("machining/<str:machine>", downtimes_entry, name='downtimes_entry'),
    path("machining/machining_export/", machining_export, name='machining_export'),
]