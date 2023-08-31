from django.urls import path

from .views import index, operators_planner, get_timeline, shift_change, intervals, process_operator, get_operators, update_deviation, absences_planner, get_absences, process_absence, get_absences_count, shift_change_multi, get_accidents, get_nearmisses

app_name = "dms"

urlpatterns = [
    path("dms/intervals", intervals, name='intervals'),
    path("dms/operators", operators_planner, name='operators'),
    path("dms/absences", absences_planner, name='absences'),
    path("dms/shift_change", shift_change, name='shift_change'),
    path("dms/shift_change_multi", shift_change_multi, name='shift_change_multi'),
    path("dms/update_deviation", update_deviation, name='update_deviation'),
    path("dms/operators/get_timeline", get_timeline, name='get_timeline'),
    path("dms/operators/process_operator", process_operator, name='process_operator'),
    path("dms/operators/process_absence", process_absence, name='process_absence'),
    path("dms/operators/get_operators", get_operators, name='get_operators'),
    path("dms/operators/get_absences", get_absences, name='get_absences'),
    path("dms/operators/get_absences_count", get_absences_count, name='get_absences_count'),
    path("dms", index, name='index'),
    path("dms/get_accidents", get_accidents, name='get_accidents'),
    path("dms/get_nearmisses", get_nearmisses, name='get_nearmisses'),
]