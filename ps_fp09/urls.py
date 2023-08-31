from django.urls import path
from .views import index, dashboard, get_chart_data, edit_chart_meta_data, svg_charts, svg_charts_fetch

app_name = "ps_fp09"

urlpatterns = [
    path('problem_solving/fp09/index', index, name='index'),
    path('problem_solving/fp09/dashboard', dashboard, name='dashboard'),
    path('problem_solving/utils/get_chart_data', get_chart_data, name='get_chart_data'),
    path('problem_solving/utils/edit_chart_meta_data', edit_chart_meta_data, name='edit_chart_meta_data'),
    path('problem_solving/fp09', svg_charts, name='svg_charts'),
    path('problem_solving/utils/svg_charts_fetch', svg_charts_fetch, name='svg_charts_fetch'),
]