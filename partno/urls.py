from django.urls import URLPattern, path

from .views import partno_view

urlpatterns = [
    path("parts", partno_view, name="parts")
]