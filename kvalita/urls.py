from django.urls import URLPattern, path

from .views import kvalita_views, noks_export, specific_nok_export


app_name = "kvalita"
urlpatterns = [
    path("kvalita/", kvalita_views, name='kvalita'),
    path("kvalita/noks_export/", noks_export, name='noks_export'),
    path("kvalita/specific_nok_export/", specific_nok_export, name='specific_nok_export')

]