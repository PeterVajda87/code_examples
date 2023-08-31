from django.urls import path
from .views import fp_lanico_performance, performance_report

app_name = "fp_lanico"
urlpatterns = [
    path('fp_lanico/performance', fp_lanico_performance, name='fp_lanico_performance'),
    path('fp_lanico/performance_report', performance_report, name='performance_report')
]