from django.urls import path

from .views import performance_report, service_book, get_downtimes, losses, prestavby, check_if_falsified

app_name = "obc4"

urlpatterns = [
    path("obc4/performance_report", performance_report, name="performance_report"),
    path('obc4/service_book', service_book, name='service_book'),
    path('obc4/get_downtimes/<str:date_from>/<str:date_to>', get_downtimes, name='get_downtimes'),
    path('obc4/losses', losses, name='losses'),
    path('obc4/check_if_falsified', check_if_falsified, name='check_if_falsified'),
    path('obc4/prestavby', prestavby, name='prestavby'),
]