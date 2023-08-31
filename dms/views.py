import datetime
import json

import dateutil.parser as dt
import pytz
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import (Deviation, DMSUser, Line, LineKPItarget,
                     OperatorsAttendance, OperatorsAbsence, ShiftLeader, Area, ShiftChange)

from accidents.models import (Accident, Nearmiss)


def intervals(request):
    
    context = {
        'lines': ShiftLeader.objects.filter(shift_leader=DMSUser.objects.get(user=request.user)).values_list('area__line__line_name', 'area__line__shift_duration', 'area__line__thingworx_name').order_by('area__line__line_name')
    }
    
    return render(request, 'dms/intervals.html', context)


@csrf_exempt
@login_required
def shift_change_multi(request):
    
    return render(request, 'dms/shift_change_multi.html', {})


@csrf_exempt
@login_required
def shift_change(request):
    all_lines = ['AoH', 'BS', 'DPA', 'NG4', 'OBC1', 'OBC3', 'OBC4', 'Wedge']

    if request.method == 'POST':
        request_data = json.loads(request.body)
        lines = request_data['line']
        
        if request_data['requested_data'] == 'shift_info':           
            shift_beginning = pytz.timezone("UTC").localize(datetime.datetime.strptime(request_data['shift-beginning'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
            shift_end = pytz.timezone("UTC").localize(datetime.datetime.strptime(request_data['shift-end'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
            
            if isinstance(request_data['line'], list) or request_data['line'] == 'all':
                shift_info = ShiftChange.objects.get(shift_line=Line.objects.get(line_name='OBC3'), shift_beginning=shift_beginning, shift_end=shift_end)
            else:
                shift_info = ShiftChange.objects.get(shift_line=Line.objects.get(line_name=request_data['line']), shift_beginning=shift_beginning, shift_end=shift_end)
                
            info_5s = shift_info.five_s_done
            text_info_1 = shift_info.text_info_1
            text_info_2 = shift_info.text_info_2
            handover_confirmed = shift_info.handover_confirmed
            
            return JsonResponse({'info_5s': info_5s, 'text_info_1': text_info_1, 'text_info_2': text_info_2, 'handover_confirmed': handover_confirmed})
        
        if request_data['requested_data'] == 'store-shift-info':
            try:
                desired_time = pytz.timezone("UTC").localize(datetime.datetime.strptime(request_data['desired-time'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
            except:
                desired_time = pytz.timezone("UTC").localize(datetime.datetime.strptime(request_data['desired-time'], '%Y-%m-%dT%H:%M'), is_dst=None)
            
            if desired_time.astimezone().hour >= 22:
                shift_start = desired_time.astimezone().replace(hour = 22, minute = 0, second=0, microsecond=0)
                shift_end = shift_start + datetime.timedelta(hours = 8)
            elif desired_time.astimezone().hour < 6:
                shift_start = (desired_time.astimezone() - datetime.timedelta(days=1)).replace(hour = 22, minute = 0, second=0, microsecond=0)
                shift_end = shift_start + datetime.timedelta(hours = 8)
            elif desired_time.astimezone().hour >= 6 and desired_time.astimezone().hour < 14:
                shift_start = desired_time.astimezone().replace(hour = 6, minute = 0, second=0, microsecond=0)
                shift_end = shift_start + datetime.timedelta(hours = 8)
            else:
                shift_start = desired_time.astimezone().replace(hour = 14, minute = 0, second=0, microsecond=0)
                shift_end = shift_start + datetime.timedelta(hours = 8)
                
            if isinstance(request_data['line'], list) or request_data['line'] == 'all':
                for line in Line.objects.filter(line_name__in=all_lines):
                    if request_data['element-name'] == "info-5s":
                        ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=line, defaults = {'five_s_done': request_data['element-value']})
                    if request_data['element-name'] == "shift-change-agreement":
                        ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=line, defaults = {'handover_confirmed': request_data['element-value']})
                    if request_data['element-name'] == "text-info-1":
                        ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=line, defaults = {'text_info_1': request_data['element-value']})
                    if request_data['element-name'] == "text-info-2":
                        ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=line, defaults = {'text_info_2': request_data['element-value']})
                        
            else:
                if request_data['element-name'] == "info-5s":
                    ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=Line.objects.get(line_name=request_data['line']), defaults = {
                    'five_s_done': request_data['element-value']})
                if request_data['element-name'] == "shift-change-agreement":
                    ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=Line.objects.get(line_name=request_data['line']), defaults = {
                    'handover_confirmed': request_data['element-value']})
                if request_data['element-name'] == "text-info-1":
                    ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=Line.objects.get(line_name=request_data['line']), defaults = {
                    'text_info_1': request_data['element-value']})
                if request_data['element-name'] == "text-info-2":
                    ShiftChange.objects.update_or_create(shift_beginning=shift_start, shift_end=shift_end, shift_line=Line.objects.get(line_name=request_data['line']), defaults = {
                    'text_info_2': request_data['element-value']})
            
            return JsonResponse({'status': 'okay'})

        if request_data['requested_data'] == 'targets':
            targets = {}
            line_targets = LineKPItarget.objects.filter(line = Line.objects.get(line_name=lines))

            for line_target in line_targets:
                if line_target.kpi.kpi_name == 'RQ':
                    targets['RQ'] = line_target.value
                if line_target.kpi.kpi_name == 'Deliveries':
                    targets['deliveries'] = line_target.value
                if line_target.kpi.kpi_name == 'Costs':
                    targets['costs'] = line_target.value
                if line_target.kpi.kpi_name == 'Safety':
                    targets['safety'] = 1
                
        
        if request_data['requested_data'] == 'line_targets':
            targets = {}
            
            for line in lines:
                targets[line] = {}
                line_targets = LineKPItarget.objects.filter(line = Line.objects.get(line_name=line))
                
                for line_target in line_targets:
                    if line_target.kpi.kpi_name == 'RQ':
                        targets[line]['RQ'] = line_target.value
                    if line_target.kpi.kpi_name == 'Deliveries':
                        targets[line]['deliveries'] = line_target.value
                    if line_target.kpi.kpi_name == 'Costs':
                        targets[line]['costs'] = line_target.value
                    if line_target.kpi.kpi_name == 'Safety':
                        targets[line]['safety'] = 1
            

        return JsonResponse(targets)
            
    
    if request.method == 'GET':
        
        context = {
            'lines': ['AoH', 'BS', 'DPA', 'NG4', 'OBC1', 'OBC3', 'OBC4', 'Wedge']
        }
    
        return render(request, 'dms/shift_change.html', context)


@login_required
def operators_planner(request):
   
    context = {
        'lines': ShiftLeader.objects.filter(shift_leader=DMSUser.objects.get(user=request.user)).values_list('area__line__line_name', 'area__line__shift_duration').order_by('area__line__line_name'),
        'area': ShiftLeader.objects.get(shift_leader=DMSUser.objects.get(user=request.user)).area.area_name
    }

    return render(request, 'dms/operators.html', context)


@login_required
def absences_planner(request):
    
    context = {
        'absence_categories': ['Dovolená', 'Nemoc', 'Náhradní volno', 'Lékař', 'Ostatní'],
        'area': ShiftLeader.objects.get(shift_leader=DMSUser.objects.get(user=request.user)).area.area_name
    }

    return render(request, 'dms/absences.html', context)


@csrf_exempt
def process_operator(request):
    data = json.loads(request.body)
    action = data['type']
    line_name = data['line']
    worker_id = data['worker_id']
    worker_type = data['worker_type']
    interval_start = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_start'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    interval_end = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_end'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    
    if action == 'addition':
        OperatorsAttendance.objects.create(line = Line.objects.get(line_name=line_name), interval_start = interval_start, interval_end = interval_end, worker_id = worker_id, worker_type = worker_type)
    
    if action == 'removal':
        OperatorsAttendance.objects.filter(line = Line.objects.get(line_name=line_name), interval_start = interval_start, interval_end = interval_end, worker_id = worker_id, worker_type = worker_type).delete()
    
    return HttpResponse('okay')


@csrf_exempt
def process_absence(request):
    data = json.loads(request.body)
    action = data['type']
    area = Area.objects.get(area_name=data['area'])
    absence_category = data['absence_category']
    worker_id = data['worker_id']
    worker_type = data['worker_type']
    interval_start = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_start'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    interval_end = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_end'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    
    if action == 'addition':
        OperatorsAbsence.objects.create(area = area, interval_start = interval_start, interval_end = interval_end, worker_id = worker_id, worker_type = worker_type, absence_category = absence_category)
    
    if action == 'removal':
        OperatorsAbsence.objects.filter(area = area, interval_start = interval_start, interval_end = interval_end, worker_id = worker_id, worker_type = worker_type, absence_category = absence_category).delete()
    
    return HttpResponse('okay')


@csrf_exempt
def get_operators(request):
    data = json.loads(request.body)
    line_name = data['line']
    interval_start = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_start'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    interval_end = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_end'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    
    data = list(OperatorsAttendance.objects.filter(line = Line.objects.get(line_name=line_name), interval_start = interval_start, interval_end = interval_end).values_list('worker_id', 'worker_type'))
        
    return JsonResponse({'data': data})


@csrf_exempt
def get_absences_count(request):
    request_data = json.loads(request.body)
    area = request_data['area']
    desired_time = dt.parse(request_data['desired-time'])
    
    if desired_time.astimezone().hour >= 22:
        timeline_start = desired_time.astimezone().replace(hour = 22, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    elif desired_time.astimezone().hour < 6:
        timeline_start = (desired_time.astimezone() - datetime.timedelta(days=1)).replace(hour = 22, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    elif desired_time.astimezone().hour >= 6 and desired_time.astimezone().hour < 14:
        timeline_start = desired_time.astimezone().replace(hour = 6, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    else:
        timeline_start = desired_time.astimezone().replace(hour = 14, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
        
    absences_hours = OperatorsAbsence.objects.filter(area = Area.objects.get(area_name=area), interval_start__gte=timeline_start, interval_end__lte=timeline_end).count()
    
    return JsonResponse({'absences': absences_hours / 8})    


@csrf_exempt
def get_absences(request):
    data = json.loads(request.body)
    absence_category = data['absence_category']
    area = data['area']
    interval_start = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_start'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    interval_end = pytz.timezone("UTC").localize(datetime.datetime.strptime(data['interval_end'], '%Y-%m-%dT%H:%M:%S.%fZ'), is_dst=None)
    
    data = list(OperatorsAbsence.objects.filter(absence_category = absence_category, area = Area.objects.get(area_name=area), interval_start = interval_start, interval_end = interval_end).values_list('worker_id', 'worker_type'))
        
    return JsonResponse({'data': data})


@csrf_exempt
def get_timeline(*args, **kwargs):
    request = args[0]
    request_data = json.loads(request.body)
    desired_time = dt.parse(request_data['desired-time'])
    
    if desired_time.astimezone().hour >= 22:
        timeline_start = desired_time.astimezone().replace(hour = 22, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    elif desired_time.astimezone().hour < 6:
        timeline_start = (desired_time.astimezone() - datetime.timedelta(days=1)).replace(hour = 22, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    elif desired_time.astimezone().hour >= 6 and desired_time.astimezone().hour < 14:
        timeline_start = desired_time.astimezone().replace(hour = 6, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    else:
        timeline_start = desired_time.astimezone().replace(hour = 14, minute = 0, second=0, microsecond=0)
        timeline_end = timeline_start + datetime.timedelta(hours = 8)
    
    timeline = {
        'start': timeline_start.isoformat(),
        'end': timeline_end.isoformat(),
    }
    
    return JsonResponse(timeline)


@login_required
def index(request):

    context = {
    }

    return render(request, 'dms/index.html', context)


@csrf_exempt
def update_deviation(request):
    if request.method == "POST":
        request_data = json.loads(request.body)
        deviation_id = request_data['deviation_id']
        
        deviation = Deviation.objects.get(deviation_id = deviation_id) if Deviation.objects.filter(deviation_id = deviation_id).exists() else Deviation.objects.create(deviation_id = deviation_id, details = {})
        
        if request_data['changed_item'] == 'deviation-category':
            deviation.details['category'] = request_data['changed_value']
        
        if request_data['changed_item'] == 'deviation-countermeasure':
            deviation.details['countermeasure'] = request_data['changed_value']
            
        if request_data['changed_item'] == 'deviation-text':
            deviation.details['text'] = request_data['changed_value']
            
        deviation.save()
            
        return JsonResponse({'status': 'okay'})
    
    if request.method == "GET":
        deviation_id = request.GET.get('deviation_id', None)
        
        deviation = Deviation.objects.get(deviation_id = deviation_id) if Deviation.objects.filter(deviation_id = deviation_id).exists() else Deviation.objects.create(deviation_id = deviation_id, details = {})
        
        serialized_deviation = json.loads(serializers.serialize('json', [deviation]))
        
        return JsonResponse(serialized_deviation[0]['fields'])
    
    
@csrf_exempt
def get_accidents(request):
    date = request.POST.get('date')
    area = request.POST.get('area')
    
    area_costcenters = {
        'BCH': [64250],
    }
    
    accidents = Accident.objects.filter(place__in=area_costcenters[area], accident_datetime__date=date)
    
    return HttpResponse(accidents.count())


@csrf_exempt
def get_nearmisses(request):
    date = request.POST.get('date')
    area = request.POST.get('area')
    
    area_costcenters = {
        'BCH': [64250],
    }

    nearmisses = Nearmiss.objects.filter(place__in=area_costcenters[area], datetime_of_nearmiss__date=date)
    return HttpResponse(nearmisses.count())