from django.urls import path
from .views import svg_charts, svg_charts_fetch

app_name = "ps_obc4"

urlpatterns = [
    path('problem_solving/obc4', svg_charts, name='svg_charts'),
    path('problem_solving/obc4/utils/svg_charts_fetch', svg_charts_fetch, name='svg_charts_fetch'),
]