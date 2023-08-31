from django.urls import URLPattern, path

from .views import changeover_view, changeover_export

app_name = "changeover"

urlpatterns = [
    path("changeover", changeover_view, name="changeover"),
    path("changeover/changeover_export/", changeover_export, name='changeover_export'),
]