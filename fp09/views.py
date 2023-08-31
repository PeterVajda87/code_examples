import datetime
import json
import operator
import random
import re
from operator import itemgetter

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import connections
from django.db.models import (Case, CharField, Count, DurationField,
                              ExpressionWrapper, F, IntegerField, Q, Sum,
                              Value, When)
from django.db.models.functions import ExtractHour, Substr, Trunc, TruncDate
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from numpy import average
from unidecode import unidecode

from thingworx.models import (FP09_alarm_description, Tb_fp09_alarms,
                              Tb_fp09_alarmstext, Tb_fp09_qd, TbFp09CtSt135)

from .models import (AddressedDowntime, CategoryColors, Counter, Downtime,
                     DowntimeFromLine, Epoch, PairedDowntime,
                     ServiceBookAction, ServiceBookActionEntry, Station,
                     StopLineAlarms, TbFp09Qd, TypeDetails)


def index(request):
    return render(request, 'fp09_index.html', {})
    

@csrf_exempt
def get_stop_line_alarms(request):

    get_stop_line_alarms_2()

    return HttpResponse('okay')

def get_stop_line_alarms_2():

    now = datetime.datetime.now()
    range_to = now.strftime("%Y-%m-%d %H:%M")
    now_delta_month = now - datetime.timedelta(weeks = 4)
    range_from = now_delta_month.strftime("%Y-%m-%d %H:%M")
    
    base_period_alarms = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lt=range_to).values_list('alarmcode', flat=True)
    stops_line_alarm_codes = list(Tb_fp09_alarmstext.objects.filter(Q(alarmtype=1) | Q(alarmtype__isnull=True)).filter(alarmcode__in=base_period_alarms).values_list('alarmcode_id', flat=True))

    for alarm_code in stops_line_alarm_codes:
        stops_line_alarm_code, created = StopLineAlarms.objects.get_or_create(alarmcode_id = alarm_code)
        result = re.search('Alarms(.*)\[', alarm_code)
        station_striped = result.group(1)
        stops_line_alarm_code.station = station_striped

        stops_line_alarm_code.save()


@csrf_exempt
def pair_downtimes(request):

    range_from = '2021-11-15 17:30'
    range_to = '2021-11-15 20:00'

    base_period_alarms = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lt=range_to).values_list('alarmcode', flat=True)

    stops_line_alarm_codes = list(Tb_fp09_alarmstext.objects.filter(Q(alarmtype=1) | Q(alarmtype__isnull=True)).filter(alarmcode__in=base_period_alarms).values_list('alarmcode_id', flat=True))
 
    actual_alarms = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=stops_line_alarm_codes).values('timestampalarm', 'alarmcode').order_by('timestampalarm')

    downtimes = DowntimeFromLine.objects.filter(beginning_t__gte=range_from, beginning_t__lt=range_to)


    for downtime in downtimes:
        paired_downtime, created = PairedDowntime.objects.get_or_create(downtime = downtime)
        actual_alarm = actual_alarms.filter(timestampalarm__lte = downtime.beginning_t).order_by('-timestampalarm').first()
        detail_actual_alarm = Tb_fp09_alarmstext.objects.filter(alarmcode=actual_alarm['alarmcode']).first()
        paired_downtime.alarm_code = actual_alarm['alarmcode']
        paired_downtime.alarm_text = detail_actual_alarm.alarmtext
        paired_downtime.alarm_type = detail_actual_alarm.alarmtype
        paired_downtime.downtime_duration = (downtime.end_t - downtime.beginning_t).total_seconds()

        paired_downtime.save()

    return HttpResponse('okay')


@csrf_exempt
def fp09_downtime_trends(request):

    if request.method == "POST":

        request_data = json.loads(request.body)
        first_interval_start = datetime.datetime.strptime(request_data['first_interval_start'], "%Y-%m-%d")
        first_interval_end = datetime.datetime.strptime(request_data['first_interval_end'], "%Y-%m-%d")
        second_interval_start = datetime.datetime.strptime(request_data['second_interval_start'], "%Y-%m-%d")
        second_interval_end = datetime.datetime.strptime(request_data['second_interval_end'], "%Y-%m-%d")
        button = request_data['button_option']
        shift = request_data['shift']
        days_first, days_in_range_first, data_first = get_data_downtime_trends(first_interval_start, first_interval_end, button, shift)
        days_second, days_in_range_second, data_second = get_data_downtime_trends(second_interval_start, second_interval_end, button, shift)
        datasets1 = []
        datasets2 = []
        used_colors = {}

        for category in data_first:
            dataset = {}
            dataset['label'] = category
            dataset['data'] = []
            dataset['tooltips'] = []
            for data in data_first[category]:
                dataset['data'].append(data[1])
            color, used_colors = setColor(category, used_colors)
            dataset['borderColor'] = color
            for data in data_first[category]:
                dataset['tooltips'].append(f"Četnost: {data[2]}|Trvání: {data[1]/60}")
            datasets1.append(dataset)

        for category in data_second:
            dataset = {}
            dataset['label'] = category
            dataset['data'] = []
            dataset['tooltips'] = []
            for data in data_second[category]:
                dataset['data'].append(data[1])
            color, used_colors = setColor(category, used_colors)
            dataset['borderColor'] = color
            for data in data_second[category]:
                dataset['tooltips'].append(f"Četnost: {data[2]}|Trvání: {data[1]/60}")
            datasets2.append(dataset)
        
        seconds_in_first_interval_without_sorting = {}
        for category in datasets1:
            category_in_iteration = category['label']
            seconds_in_first_interval_without_sorting[category_in_iteration] = sum(category['data']) / 60 # na minuty
        
        seconds_in_first_interval = dict(sorted(seconds_in_first_interval_without_sorting.items(), key=operator.itemgetter(1), reverse=True))

        seconds_in_second_interval_without_sorting = {}
        for category in datasets2:
            category_in_iteration = category['label']
            seconds_in_second_interval_without_sorting[category_in_iteration] = sum(category['data']) / 60 # na minuty

        seconds_in_second_interval = dict(sorted(seconds_in_second_interval_without_sorting.items(), key=operator.itemgetter(1),reverse=True))

        keys_in_intervals = [*seconds_in_first_interval]
        for key in seconds_in_second_interval:
            if key not in keys_in_intervals:
                keys_in_intervals.append(key)
        
        barchart_dict = {}
        for key in keys_in_intervals:
            barchart_dict[key] = []
            time = 0
            if key in seconds_in_first_interval:
                time += seconds_in_first_interval[key]
            if key in seconds_in_second_interval:
                time += seconds_in_second_interval[key]
            barchart_dict[key].append(time)
            if key in seconds_in_first_interval:
                barchart_dict[key].append(seconds_in_first_interval[key])
            else:
                barchart_dict[key].append(0)
            if key in seconds_in_second_interval:
                barchart_dict[key].append(seconds_in_second_interval[key])
            else:
                barchart_dict[key].append(0)
        
        barchart_dict = dict(sorted(barchart_dict.items(), key=operator.itemgetter(1),reverse=True))

        return_data = {
            'days_first': days_first,
            'days_in_range_first': days_in_range_first,
            'datasets1': datasets1,
            'days_second': days_second,
            'days_in_range_second': days_in_range_second,
            'datasets2': datasets2,
            'barchart_dict': barchart_dict
        }
        return JsonResponse(return_data)

    if request.method == "GET":

        return render(request, 'fp09_downtime_trends.html')

@csrf_exempt
def fetch_test(request):

    return render(request, 'fetch_test.html', {})

@csrf_exempt
def sync_databases(request):
    data_111 = list(Tb_fp09_alarmstext.objects.all().values())
    data_dict = {}

    for row in data_111:
        data_dict[row['alarmcode_id']] = row['alarmtext']

    local_data = FP09_alarm_description.objects.all()

    for row in local_data:
        try:
            row.description = data_dict[row.code]
            row.save()
        except:
            pass

    for code, text in data_dict.items():
        if not FP09_alarm_description.objects.filter(code=code).exists():
            FP09_alarm_description.objects.create(code=code, description=text)

    return HttpResponse('okay')



@csrf_exempt
def get_fp09_alarm_stats(request):

    shifts_per_day = 3

    if shifts_per_day == 3:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
        afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    if shifts_per_day == 2:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        afternoon_shift_hours = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]

    data = json.loads(request.body)

    shifts = data['shift']
    stops_line = data['stops_line'] # jenom pro automaticke prostoje
    does_not_stop_line = data['does_not_stop_line'] # jenom pro automaticke prostoje
    informs_line = data['informs_line'] # jenom pro automaticke prostoje

    if 'count_of' in data: # tohle je pro top 10, 15, 20
        count_of = int(data['count_of']) # tohle je pro top 10, 15, 20
    else: # tohle je pro top 10, 15, 20
        count_of = 10 # tohle je pro top 10, 15, 20

    if shifts == 'All':
        if shifts_per_day == 3:
            shifts = ['Morning', 'Afternoon', 'Night']
        if shifts_per_day == 2:
            shifts = ['Morning', 'Afternoon']

    else:
        shifts = [shifts]

    range_to = datetime.date.today() - datetime.timedelta(days = 1)
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(range_to, time_to)
    range_from = range_to - datetime.timedelta(days = int(data['days']))

    if 'start_date' in data:
        datetime_from = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
        if shifts_per_day == 3:
            time_from = datetime.time(22,0,0)
            range_from = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)
        if shifts_per_day == 2:
            time_from = datetime.time(6, 0, 0)
            range_from = datetime.datetime.combine(datetime_from, time_from)

    if 'end_date' in data:
        datetime_to = datetime.datetime.strptime(data['end_date'], "%Y-%m-%d")
        if shifts_per_day == 3:
            time_to = datetime.time(22,0,0)
            range_to = datetime.datetime.combine(datetime_from, time_from)
        if shifts_per_day == 2:
            time_to = datetime.time(6, 0, 0)
            range_to = datetime.datetime.combine(datetime_from + datetime.timedelta(days=1), time_from)

    actual_alarms = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to).values_list('alarmcode', flat=True) # jenom pro automaticke prostoje

    stops_line_alarms = list(Tb_fp09_alarmstext.objects.filter(Q(alarmtype=1) | Q(alarmtype__isnull=True)).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True)) # jenom pro automaticke prostoje
    slows_line_alarms = list(Tb_fp09_alarmstext.objects.filter(alarmtype=2).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True)) # jenom pro automaticke prostoje
    informs_line_alarms =  list(Tb_fp09_alarmstext.objects.filter(alarmtype=3).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True)) # jenom pro automaticke prostoje

    alarms_included = [] # jenom pro automaticke prostoje

    if stops_line: # jenom pro automaticke prostoje
        alarms_included.extend(stops_line_alarms) # jenom pro automaticke prostoje

    if does_not_stop_line: # jenom pro automaticke prostoje
        alarms_included.extend(slows_line_alarms) # jenom pro automaticke prostoje

    if informs_line: # jenom pro automaticke prostoje
        alarms_included.extend(informs_line_alarms) # jenom pro automaticke prostoje

    production_statistics = TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(day=Trunc('productiontime', 'day')).values('day').annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(total_parts=Count('dsid')).order_by('day')

    production_statistics_for_pareto = TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total_parts=Count('dsid'))['total_parts']

    downtime_statistics = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarms_included).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('alarmcode').annotate(duration=Sum('alarmtime')).annotate(alarm_count=Count('alarmtime')).exclude(duration__isnull=True).order_by('-duration').values_list('alarmcode', 'duration', 'alarm_count'))

    downtime_statistics_relative = sorted(downtime_statistics, key = lambda tup: tup[2], reverse=True)[:count_of]
    downtime_statistics_duration = sorted(downtime_statistics, key = lambda tup: tup[1], reverse=True)[:count_of]

    if data['type'] == 'individual_relative_pareto':

        results = [(FP09_alarm_description.objects.get(code=alarm_code).description, duration / 60_000, alarm_count) for (alarm_code, duration, alarm_count) in downtime_statistics_relative]  
  
        results_data = [(key, val0, val1 / production_statistics_for_pareto, val1) if val0 is not None else (key, 0, 0) for (key, val0, val1) in results]
 
        results_data.sort(key = lambda tup: tup[2], reverse=True)

        data_data = [(key, val1) for (key, val0, val1, val2) in results_data]

        tooltips_data = [f"Četnost: {val2}|Trvání: {round(val0)}" for (key, val0, val1, val2) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }

    if data['type'] == 'individual_relative_line':

        alarm_reasons = [code for (code, total, alarm_duration) in downtime_statistics_relative]

        downtime_statistics_daily = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarm_reasons).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(day=Trunc('timestampalarm', 'day')).values('day', 'alarmcode').annotate(duration=Sum('alarmtime'), alarm_count=Count('alarmtime')).order_by('day', '-duration').values_list('day', 'alarmcode', 'duration', 'alarm_count'))
        production_statistics_daily = list(TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(day=Trunc('productiontime', 'day')).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('day').annotate(total_parts=Count('dsid')).order_by('day').values_list('total_parts', flat=True))

        days = set()
        datasets = []

        for dict_data in list(production_statistics):
            days.add(dict_data['day'].date())

        days = sorted(days)
        for alarm_reason in alarm_reasons:
            dataset = {}
            dataset['label'] = Tb_fp09_alarmstext.objects.get(alarmcode_id=alarm_reason).alarmtext if Tb_fp09_alarmstext.objects.filter(alarmcode_id=alarm_reason).exists() else "Neznámý"

            dataset['data'] = [(dt.date(), duration, alarm_count) for (dt, code, duration, alarm_count) in downtime_statistics_daily if (code == alarm_reason and dt.date() in days)]
    
            dataset['borderColor'] = 'rgb(255,255,255)'

            if len(days) > len(dataset['data']):
                days_in_alarms = (dt for (dt, duration, alarm_count) in dataset['data'])
                missing_days = set(days) - set(days_in_alarms)
                for missing_day in missing_days:
                    dataset['data'].append((missing_day, 0, 0))
                
                dataset['data'].sort(key = lambda tup: tup[0])

            for index, day in enumerate(days):
                dataset['data'][index] = (dataset['data'][index][0], dataset['data'][index][1], dataset['data'][index][2] / production_statistics_daily[index],  dataset['data'][index][2])

            dataset['tooltips'] = [f"Četnost: {raw_count}|Trvání: {round(duration / 60_000)}" if duration is not None else (duration, alarm_count) for (dt, duration, alarm_count, raw_count) in dataset['data']]

            dataset['data'] = [alarm_count if alarm_count is not None else 0 for (dt, duration, alarm_count, raw_count) in dataset['data']]

            datasets.append(dataset)
            
        return_data = {
            'days': data['days'],
            'days_in_range': days,
            'datasets': datasets,
        }

    
    if data['type'] == 'individual_pareto':

        results = [(FP09_alarm_description.objects.get(code=alarm_code).description, duration / 60_000, alarm_count) for (alarm_code, duration, alarm_count) in downtime_statistics_duration]  

        results_data = [(key, val0, val1) if val0 is not None else (key, 0, 0) for (key, val0, val1) in results]

        results_data.sort(key = lambda tup: tup[1], reverse=True)

        data_data = [(key, val0) for (key, val0, val1) in results_data]
        tooltips_data = [f"Četnost: {val1}|Trvání: {round(val0)}" for (key, val0, val1) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }

    if data['type'] == 'individual_line':

        alarm_reasons = [code for (code, total, alarm_duration) in downtime_statistics_duration]

        downtime_statistics_daily = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarm_reasons).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(day=Trunc('timestampalarm', 'day')).values('day', 'alarmcode').annotate(duration=Sum('alarmtime'), alarm_count=Count('alarmtime')).order_by('day', '-duration').values_list('day', 'alarmcode', 'duration', 'alarm_count'))

        days = set()
        datasets = []

        for dict_data in list(production_statistics):
            days.add(dict_data['day'].date())

        days = sorted(days)
            
        for alarm_reason in alarm_reasons:
            dataset = {}
            dataset['label'] = Tb_fp09_alarmstext.objects.get(alarmcode_id=alarm_reason).alarmtext if Tb_fp09_alarmstext.objects.filter(alarmcode_id=alarm_reason).exists() else "Neznámý"
            dataset['data'] = [(dt.date(), duration, alarm_count) for (dt, code, duration, alarm_count) in downtime_statistics_daily if (code == alarm_reason and dt.date() in days)]

            dataset['borderColor'] = 'rgb(255,255,255)'

            if len(days) > len(dataset['data']):
                days_in_alarms = (dt for (dt, duration, alarm_count) in dataset['data'])
                missing_days = set(days) - set(days_in_alarms)
                for missing_day in missing_days:
                    dataset['data'].append((missing_day, 0, 0))
                
                dataset['data'].sort(key = lambda tup: tup[0])
            
            dataset['tooltips'] = [f"Četnost: {alarm_count}|Trvání: {round(duration / 60_000)}" if duration is not None else (duration, alarm_count) for (dt, duration, alarm_count) in dataset['data']]

            dataset['data'] = [(duration / 60_000) if duration is not None else duration for (dt, duration, alarm_count) in dataset['data']]

            datasets.append(dataset)
            
        return_data = {
            'days': data['days'],
            'days_in_range': days,
            'datasets': datasets,
        }

    if data['type'] == 'group_pareto':

        results = {}

        groups = FP09_alarm_description.objects.all().values_list('group', flat=True).exclude(group='').distinct('group')

        for group in groups:
            group_alarm_codes = list(FP09_alarm_description.objects.filter(group=group).values_list('code', flat=True))
            results[group] = (
                Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total=Sum('alarmtime'))['total'],
                Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total=Count('alarmtime'))['total']
            )

        results_data = [(key, value[0] / 60_000, value[1]) if value[0] is not None else (key, 0, 0) for (key, value) in results.items()]

        results_data.sort(key = lambda tup: tup[1], reverse=True)

        data_data = [(key, val0) for (key, val0, val1) in results_data]
        tooltips_data = [f"Četnost: {val1}|Trvání: {round(val0)}" for (key, val0, val1) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }

    if data['type'] == 'group_line':

        days = set()

        for dict_data in list(production_statistics):
            days.add(dict_data['day'])

        days = sorted(days)

        datasets = []
        
        groups = FP09_alarm_description.objects.all().values_list('group', flat=True).exclude(group='').distinct('group')

        results = {}

        for group in groups:
            group_alarm_codes = list(FP09_alarm_description.objects.filter(group=group).values_list('code', flat=True))
            results[group] = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(day=Trunc('timestampalarm', 'day')).order_by('day').values('day').annotate(duration=Sum('alarmtime'), alarm_count=Count('alarmtime')).values_list('day', 'duration', 'alarm_count'))

            group_alarm_dates = [tup[0] for tup in results[group]]

            for day in days:
                if not day in group_alarm_dates:
                    results[group].append((day, 0, 0))

            results[group].sort(key = lambda tup: tup[0])

            results[group] = [(to_minutes(tup[1]), tup[2]) for tup in results[group] if tup[0] in days]                

        
        for group, values in results.items():
            dataset = {}
            dataset['label'] = group
            dataset['data'] = [num[0] for num in values]
            dataset['tooltips'] = [f"Četnost: {num[1]}|Trvání: {round(num[0])}" for num in values]
            dataset['borderColor'] = 'rgb(255,255,255)'
            datasets.append(dataset)

        return_data = {
            'days': data['days'],
            'days_in_range': [day.date() for day in days],
            'datasets': datasets,
        }
    
    return JsonResponse(return_data)


def to_minutes(tup_val):
    if tup_val:
        return (tup_val / 60_000)
    return 0


@csrf_exempt
def alarm_stats(request):

    colors = list(FP09_alarm_description.objects.all().values('description', 'color_code'))
    group_colors = list(FP09_alarm_description.objects.all().values('group', 'color_code'))

    color_codes = {}

    for item in colors:
        color_codes[item['description']] = item['color_code']
        color_codes[item['description'][:25]] = item['color_code']

    for item in group_colors:
        color_codes[item['group']] = item['color_code']
        color_codes[item['group'][:25]] = item['color_code']

    context = {
        'colors': color_codes,
    }

    return render(request, 'fp09_alarms_stats.html', context)


@csrf_exempt
def pareto_screen_fp09(request):
    shifts_per_day = 3

    if shifts_per_day == 3:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
        afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    if shifts_per_day == 2:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        afternoon_shift_hours = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]

    if request.method == "POST":

        request_data = json.loads(request.body)

        shifts = request_data['shift']

        if shifts_per_day == 3:
            if shifts == 'All':
                shifts = ['Morning', 'Afternoon', 'Night']
            else:
                shifts = [shifts]

        if shifts_per_day == 2:
            if shifts == 'All':
                shifts = ['Morning', 'Afternoon']
            else:
                shifts = [shifts]


        datetime_from = datetime.datetime.strptime(request_data['date_from'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
        datetime_to = datetime.datetime.strptime(request_data['date_to'], "%Y-%m-%d") ## predpoklada den do 22:00

        if shifts_per_day == 3:
            time_from = datetime.time(22,0,0)
            time_to = datetime.time(22,0,0)
        if shifts_per_day == 2:
            time_from = datetime.time(6,0,0)
            time_to = datetime.time(6,0,0)

        if shifts_per_day == 3:
            datetime_from = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)
            datetime_to = datetime.datetime.combine(datetime_to, time_to)
        if shifts_per_day == 2:
            datetime_from = datetime.datetime.combine(datetime_from, time_from)
            datetime_to = datetime.datetime.combine(datetime_to + datetime.timedelta(days = 1), time_to)


        return_data = {}

        if request_data['type'] == 'downtimes_overall':

            data_per_category = DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from, beginning_t__lt=datetime_to).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).values('category').annotate(sum_of_durations=Sum('duration')).order_by('-sum_of_durations').values_list('category', 'sum_of_durations')

            labels_categories, data_categories = zip(*data_per_category)

            categories_colors = []
            for category in labels_categories:
                categories_colors.append(CategoryColors.objects.get(category=category).color_code if CategoryColors.objects.filter(category=category).exists() else 'rgba(255,0,0,0.5)')

            return_data['data'] = [round(value.total_seconds() / 60, 1) if value else (0, 1) for value in data_categories]
            return_data['backgroundColor'] = categories_colors
            return_data['labels'] = [label for label in labels_categories]

            return JsonResponse(return_data)

        else:
            category = request_data['type']

            data_per_downtime_reason = list(DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from, end_t__lt=datetime_to, category=category).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).annotate(short_downtime=Substr('downtime', 1, 40)).values('short_downtime').annotate(sum_of_durations=Sum('duration')).order_by('-sum_of_durations').values_list('short_downtime', 'sum_of_durations')[:6])
            labels_reasons = []
            data_reasons = []

            for short_downtime, delta_time in data_per_downtime_reason:
                labels_reasons.append(short_downtime if short_downtime else "N/A")
                data_reasons.append(delta_time)
            category_color = CategoryColors.objects.get(category=category).color_code if CategoryColors.objects.filter(category=category).exists() else 'rgba(255,0,0,0.5)'

            reasons_colors = []
            for reason in labels_reasons:
                reasons_colors.append(category_color)

            return_data['data'], return_data['category'], return_data['backgroundColor'], return_data['labels'], return_data['title'] = [round(value.total_seconds() / 60, 1) for value in data_reasons], category, reasons_colors, labels_reasons, category
            return JsonResponse(return_data)


    if request.method == "GET":
        return render(request, 'pareto_screen_fp09.html', context = {})
    

@csrf_exempt
def performance_screen_fp09(request):

    shifts_per_day = 3
    
    if shifts_per_day == 3:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
        afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]
    if shifts_per_day == 2:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        afternoon_shift_hours = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]


    if request.method == "POST":
        request_data = json.loads(request.body)

        shifts = request_data['shift']

        if shifts_per_day == 3:
            if shifts == 'All':
                shifts = ['Morning', 'Afternoon', 'Night']
            else:
                shifts = [shifts]

        if shifts_per_day == 2:
            if shifts == 'All':
                shifts = ['Morning', 'Afternoon']
            else:
                shifts = [shifts]
            
        TAKT = 4.1/60

        if request_data['type'] == 'performance_chart':

            LOGISTIC_CATEGORIES = ['Input components + packaging / Vstupní komponenty + balení', 'Logistic / Logistika']
            ORGANIZATIONAL_CATEGORIES = ['Organization / Organizace']
            TECHNICAL_CATEGORIES = ['Repair, maintenance / Oprava, údržba', 'Technical downtime / technický prostoj']

            datetime_from = datetime.datetime.strptime(request_data['date_from'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
            datetime_to = datetime.datetime.strptime(request_data['date_to'], "%Y-%m-%d") ## predpoklada den do 22:00
            if shifts_per_day == 3:
                time_from = datetime.time(22,0,0)
                time_to = datetime.time(22,0,0)
            if shifts_per_day == 2:
                time_from = datetime.time(6,0,0)
                time_to = datetime.time(6,0,0)

            if shifts_per_day == 3:
                datetime_from_dt = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to, time_to)
            if shifts_per_day == 2:
                datetime_from_dt = datetime.datetime.combine(datetime_from, time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to + datetime.timedelta(days = 1), time_to)

            labels = []
            datasets = []

            dataset_production_of_ok_pieces = {}
            dataset_production_of_ok_pieces['label'] = 'Production of OK parts'
            dataset_production_of_ok_pieces['data'] = []
            dataset_production_of_ok_pieces['backgroundColor'] = 'rgba(0,255,0,0.5)'
            dataset_quality_loss = {}
            dataset_quality_loss['label'] = 'Quality loss'
            dataset_quality_loss['data'] = []
            dataset_quality_loss['backgroundColor'] = 'rgba(255,0,0,0.5)'
            dataset_logistics_loss = {}
            dataset_logistics_loss['label'] = 'Logistics loss'
            dataset_logistics_loss['data'] = []
            dataset_logistics_loss['backgroundColor'] = 'rgba(0,0,255,0.5)'
            dataset_null_loss = {}
            dataset_null_loss['label'] = 'Unexplained loss'
            dataset_null_loss['data'] = []
            dataset_null_loss['backgroundColor'] = 'rgba(0,0,0,0.5)'
            dataset_organizational_loss = {}
            dataset_organizational_loss['label'] = 'Organizational loss'
            dataset_organizational_loss['data'] = []
            dataset_organizational_loss['backgroundColor'] = 'rgba(255,255,0,0.5)'
            dataset_technical_loss = {}
            dataset_technical_loss['label'] = 'Technical loss'
            dataset_technical_loss['data'] = []
            dataset_technical_loss['backgroundColor'] = 'rgba(0,255,255,0.5)'
            dataset_performance_loss = {}
            dataset_performance_loss['label'] = 'Performance loss'
            dataset_performance_loss['data'] = [] 
            dataset_performance_loss['backgroundColor'] = 'rgba(125,125,125,0.5)'

            while datetime_from_dt <= datetime_to_dt - datetime.timedelta(days=1):

                # labels.append(str((datetime_from_dt + datetime.timedelta(days=1)).date()))
                labels.append(str(datetime_from_dt.date()))

                if len(shifts) == 3:
                    period_minutes = ((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60
                else:
                    if shifts_per_day == 2:
                        period_minutes = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60) / 2 * len(shifts)
                    if shifts_per_day == 3:
                        period_minutes = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60) / 3 * len(shifts)

                produced_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).values('formerstation', 'dsid', 'partstatus', 'productiontime').filter(Q(formerstation=130) | (Q(formerstation=135) & Q(partstatus__in=["89", "105"]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(produced_pieces=Count('dsid'))['produced_pieces']

                nok_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).values('formerstation', 'productiontime', 'partstatus').filter(Q(formerstation__lt=130) | (Q(formerstation=130) & ~Q(partstatus__in=[25, 41])) | (Q(formerstation=135) & ~Q(partstatus__in=[89, 105]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('formerstation').aggregate(nok_pieces=Count('formerstation'))['nok_pieces']

                dataset_production_of_ok_pieces['data'].append((produced_pieces * TAKT) / period_minutes)

                dataset_quality_loss['data'].append((nok_pieces * TAKT) / period_minutes)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=LOGISTIC_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_logistics_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=LOGISTIC_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(logistics_loss=Sum('duration'))['logistics_loss'].total_seconds() / 60) / period_minutes)
                else:
                    dataset_logistics_loss['data'].append(0)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=ORGANIZATIONAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_organizational_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=ORGANIZATIONAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(organizational_loss=Sum('duration'))['organizational_loss'].total_seconds() / 60) / period_minutes)
                else:
                    dataset_organizational_loss['data'].append(0)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=TECHNICAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_technical_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=TECHNICAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(technical_loss=Sum('duration'))['technical_loss'].total_seconds() / 60) / period_minutes)
                else:
                    dataset_technical_loss['data'].append(0)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__isnull=True).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_null_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__isnull=True).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(technical_loss=Sum('duration'))['technical_loss'].total_seconds() / 60) / period_minutes)
                else:
                    dataset_null_loss['data'].append(0)

                dataset_performance_loss['data'].append(1 - dataset_production_of_ok_pieces['data'][-1] - dataset_quality_loss['data'][-1] - dataset_logistics_loss['data'][-1] - dataset_organizational_loss['data'][-1] - dataset_technical_loss['data'][-1] - dataset_null_loss['data'][-1])

                datetime_from_dt += datetime.timedelta(days=1)
            
            datasets.append(dataset_production_of_ok_pieces)
            datasets.append(dataset_quality_loss)
            datasets.append(dataset_logistics_loss)
            datasets.append(dataset_organizational_loss)
            datasets.append(dataset_technical_loss)
            datasets.append(dataset_performance_loss)
            datasets.append(dataset_null_loss)

            return JsonResponse({
                'datasets': datasets,
                'labels': labels,
                })

        if request_data['type'] == 'performance_hourly_chart':

            LOGISTIC_CATEGORIES = ['Input components + packaging / Vstupní komponenty + balení', 'Logistic / Logistika']
            ORGANIZATIONAL_CATEGORIES = ['Organization / Organizace']
            TECHNICAL_CATEGORIES = ['Repair, maintenance / Oprava, údržba', 'Technical downtime / technický prostoj']

            datetime_from = datetime.datetime.strptime(request_data['date_from'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
            datetime_to = datetime.datetime.strptime(request_data['date_to'], "%Y-%m-%d") ## predpoklada den do 22:00

            if shifts_per_day == 3:
                time_from = datetime.time(22,0,0)
                time_to = datetime.time(22,0,0)
                datetime_from_dt = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to, time_to)
            if shifts_per_day == 2:
                time_from = datetime.time(6,0,0)
                time_to = datetime.time(6,0,0)
                datetime_from_dt = datetime.datetime.combine(datetime_from, time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to + datetime.timedelta(days = 1), time_to)
            
            labels = []
            datasets = []

            dataset_production_of_ok_pieces = {}
            dataset_production_of_ok_pieces['label'] = 'Production of OK parts'
            dataset_production_of_ok_pieces['data'] = []
            dataset_production_of_ok_pieces['backgroundColor'] = 'rgba(0,255,0,0.5)'
            dataset_quality_loss = {}
            dataset_quality_loss['label'] = 'Quality loss'
            dataset_quality_loss['data'] = []
            dataset_quality_loss['backgroundColor'] = 'rgba(255,0,0,0.5)'
            dataset_logistics_loss = {}
            dataset_logistics_loss['label'] = 'Logistics loss'
            dataset_logistics_loss['data'] = []
            dataset_logistics_loss['backgroundColor'] = 'rgba(0,0,255,0.5)'
            dataset_organizational_loss = {}
            dataset_organizational_loss['label'] = 'Organizational loss'
            dataset_organizational_loss['data'] = []
            dataset_organizational_loss['backgroundColor'] = 'rgba(255,255,0,0.5)'
            dataset_null_loss = {}
            dataset_null_loss['label'] = 'Unexplained loss'
            dataset_null_loss['data'] = []
            dataset_null_loss['backgroundColor'] = 'rgba(0,0,0,0.5)'
            dataset_technical_loss = {}
            dataset_technical_loss['label'] = 'Technical loss'
            dataset_technical_loss['data'] = []
            dataset_technical_loss['backgroundColor'] = 'rgba(0,255,255,0.5)'
            dataset_performance_loss = {}
            dataset_performance_loss['label'] = 'Performance loss'
            dataset_performance_loss['data'] = [] 
            dataset_performance_loss['backgroundColor'] = 'rgba(125,125,125,0.5)'

            while datetime_from_dt <= datetime_to_dt - datetime.timedelta(days=1):

                # labels.append(str((datetime_from_dt + datetime.timedelta(days=1)).date()))
                labels.append(str(datetime_from_dt.date()))

                if len(shifts) == 3:
                    period_minutes = ((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60
                    period_hours = ((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 3600
                else:
                    if shifts_per_day == 3:
                        period_minutes = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60) / 3
                        period_hours = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 3600) / 3
                    if shifts_per_day == 2:
                        period_minutes = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 60) / 2 * len(shifts)
                        period_hours = (((datetime_from_dt + datetime.timedelta(days=1)) - datetime_from_dt).total_seconds() / 3600) / 2 * len(shifts)

                produced_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).filter(Q(formerstation=130) | (Q(formerstation=135) & Q(partstatus__in=[89, 105]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(part_qty=Count('dsid'))['part_qty']

                nok_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).values('formerstation', 'productiontime', 'partstatus').filter(Q(formerstation__lt=130) | (Q(formerstation=130) & ~Q(partstatus__in=[25, 41])) | (Q(formerstation=135) & ~Q(partstatus__in=[89, 105]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('formerstation').aggregate(nok_pieces=Count('formerstation'))['nok_pieces']

                dataset_production_of_ok_pieces['data'].append((produced_pieces * TAKT) / 60)

                dataset_quality_loss['data'].append((nok_pieces * TAKT) / 60)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=LOGISTIC_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_logistics_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=LOGISTIC_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(logistics_loss=Sum('duration'))['logistics_loss'].total_seconds() / 3600))
                else:
                    dataset_logistics_loss['data'].append(0)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=ORGANIZATIONAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_organizational_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=ORGANIZATIONAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(organizational_loss=Sum('duration'))['organizational_loss'].total_seconds() / 3600))
                else:
                   dataset_organizational_loss['data'].append(0) 

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=TECHNICAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_technical_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category__in=TECHNICAL_CATEGORIES).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(technical_loss=Sum('duration'))['technical_loss'].total_seconds() / 3600))
                else:
                    dataset_technical_loss['data'].append(0)

                dataset_performance_loss['data'].append(period_hours - dataset_production_of_ok_pieces['data'][-1] - dataset_quality_loss['data'][-1] - dataset_logistics_loss['data'][-1] - dataset_organizational_loss['data'][-1] - dataset_technical_loss['data'][-1])

                datetime_from_dt += datetime.timedelta(days=1)
            
            datasets.append(dataset_production_of_ok_pieces)
            datasets.append(dataset_quality_loss)
            datasets.append(dataset_logistics_loss)
            datasets.append(dataset_organizational_loss)
            datasets.append(dataset_technical_loss)
            datasets.append(dataset_performance_loss)

            return JsonResponse({
                'datasets': datasets,
                'labels': labels,
                })

        if request_data['type'] == 'ok_production_co_loss_chart':
            datetime_from = datetime.datetime.strptime(request_data['date_from'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
            datetime_to = datetime.datetime.strptime(request_data['date_to'], "%Y-%m-%d") ## predpoklada den do 22:00

            if shifts_per_day == 3:
                time_from = datetime.time(22,0,0)
                time_to = datetime.time(22,0,0)
                datetime_from_dt = datetime.datetime.combine(datetime_from - datetime.timedelta(days=1), time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to, time_to)

            if shifts_per_day == 2:
                time_from = datetime.time(6,0,0)
                time_to = datetime.time(6,0,0)
                datetime_from_dt = datetime.datetime.combine(datetime_from, time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to + datetime.timedelta(days = 1), time_to)
            
            labels = []
            datasets = []

            dataset_production_of_ok_pieces = {}
            dataset_production_of_ok_pieces['label'] = 'Production of OK parts'
            dataset_production_of_ok_pieces['data'] = []
            dataset_production_of_ok_pieces['backgroundColor'] = 'rgba(0,255,0,0.5)'
            dataset_co_loss = {}
            dataset_co_loss['label'] = 'Changeover loss'
            dataset_co_loss['data'] = []
            dataset_co_loss['backgroundColor'] = 'rgba(255,0,0,0.5)'

            while datetime_from_dt <= datetime_to_dt - datetime.timedelta(days=1):

                # labels.append(str((datetime_from_dt + datetime.timedelta(days=1)).date()))
                labels.append(str(datetime_from_dt.date()))

                produced_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).filter(Q(formerstation=130) | (Q(formerstation=135) & Q(partstatus__in=["89", "105"]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(produced_pieces=Count('dsid'))['produced_pieces']

                dataset_production_of_ok_pieces['data'].append((produced_pieces or 0) * TAKT)

                if DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category='Changeover / Přestavba').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exists():
                    dataset_co_loss['data'].append((DowntimeFromLine.objects.filter(beginning_t__gte=datetime_from_dt, end_t__lt=datetime_from_dt + datetime.timedelta(days=1), category='Changeover / Přestavba').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).aggregate(co_loss=Sum('duration'))['co_loss'].total_seconds() / 60))
                else:
                    dataset_co_loss['data'].append(0)

                datetime_from_dt += datetime.timedelta(days=1)

            datasets.append(dataset_production_of_ok_pieces)
            datasets.append(dataset_co_loss)

            return JsonResponse({
                'datasets': datasets,
                'labels': labels,
                })

        if request_data['type'] == 'ok_nok_chart':
            datetime_from = datetime.datetime.strptime(request_data['date_from'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
            datetime_to = datetime.datetime.strptime(request_data['date_to'], "%Y-%m-%d") ## predpoklada den do 22:00
            
            if shifts_per_day == 3:
                time_from = datetime.time(22,0,0)
                time_to = datetime.time(22,0,0)
                datetime_from_dt = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to, time_to)
            
            if shifts_per_day == 2:
                time_from = datetime.time(6,0,0)
                time_to = datetime.time(6,0,0)
                datetime_from_dt = datetime.datetime.combine(datetime_from, time_from)
                datetime_to_dt = datetime.datetime.combine(datetime_to + datetime.timedelta(days = 1), time_to)
            
            labels = []
            datasets = []

            dataset_production_of_ok_pieces = {}
            dataset_production_of_ok_pieces['label'] = 'OK parts'
            dataset_production_of_ok_pieces['data'] = []
            dataset_production_of_ok_pieces['backgroundColor'] = 'rgba(0,255,0,0.5)'
            dataset_production_of_nok_pieces = {}
            dataset_production_of_nok_pieces['label'] = 'NOK parts'
            dataset_production_of_nok_pieces['data'] = []
            dataset_production_of_nok_pieces['backgroundColor'] = 'rgba(255,0,0,0.5)'

            while datetime_from_dt <= datetime_to_dt - datetime.timedelta(days=1):

                # labels.append(str((datetime_from_dt + datetime.timedelta(days=1)).date()))
                labels.append(str(datetime_from_dt.date()))
                
                produced_ok_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).filter(Q(formerstation=130) | (Q(formerstation=135) & Q(partstatus__in=[89, 105]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(part_qty=Count('dsid'))['part_qty']

                produced_nok_pieces = TbFp09Qd.objects.filter(productiontime__gte=datetime_from_dt, productiontime__lte=datetime_from_dt + datetime.timedelta(days=1)).values('formerstation', 'productiontime', 'partstatus').filter(Q(formerstation__lt=130) | (Q(formerstation=130) & ~Q(partstatus__in=[25, 41])) | (Q(formerstation=135) & ~Q(partstatus__in=[89, 105]))).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('formerstation').aggregate(nok_pieces=Count('formerstation'))['nok_pieces']

                dataset_production_of_ok_pieces['data'].append(produced_ok_pieces)
                dataset_production_of_nok_pieces['data'].append(produced_nok_pieces)

                datetime_from_dt += datetime.timedelta(days=1)

            datasets.append(dataset_production_of_ok_pieces)
            datasets.append(dataset_production_of_nok_pieces)

            return JsonResponse({
                'datasets': datasets,
                'labels': labels,
                })

    if request.method == "GET":
        pass

    return render(request, 'performance_screen_fp09.html', context = {})


@csrf_exempt
def operator_screen(request):

    if request.method == "GET":
        stations = Downtime.objects.values_list('station', flat=True).distinct().order_by('-station')
        downtime_reasons = Downtime.objects.all().order_by('name').values('name', 'station', 'category')
        categories = Downtime.objects.all().values_list('category', flat=True).distinct()
        stations_categories = {}

        for station in stations:
            stations_categories[station] = list(Downtime.objects.filter(station=station).values_list('category', flat=True).distinct())

        context = {
            'stations': stations,
            'downtime_reasons': downtime_reasons,
            'categories': categories,
            'stations_categories': stations_categories,
        }

    if request.method == "POST":
        data = json.loads(request.body)
        end = data['end']
        start = data['beginning']
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        # if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
        #     end_dt = end_dt + datetime.timedelta(days=1)

        if start_dt.time() > end_dt.time():
            end_dt = end_dt + datetime.timedelta(days=1)

        DowntimeFromLine.objects.update_or_create(uid=data['uid'], defaults={'station': data['station'], 'category': data['category'], 'downtime': data['downtime'], 'beginning_t': data['beginning'], 'comment': data['comment'], 'end_t': end_dt})
        
        return HttpResponse("ok")

    return render(request, 'operator.html', context)


@csrf_exempt
def operator_screen_new(request):

    if request.method == "GET":
        stations = Downtime.objects.values_list('station', flat=True).distinct().order_by('station')
        downtime_reasons = list(Downtime.objects.all().values('name', 'station', 'category'))
        categories = list(Downtime.objects.all().values_list('category', flat=True).distinct())
        stations_categories = {}

        downtimes = DowntimeFromLine.objects.filter(beginning_t__gte=datetime.datetime.now() - datetime.timedelta(hours=24)).order_by('-beginning_t')

        for station in stations:
            stations_categories[station] = list(Downtime.objects.filter(station=station).values_list('category', flat=True).distinct())

        context = {
            'stations': stations,
            'downtime_reasons': downtime_reasons,
            'categories': categories,
            'stations_categories': stations_categories,
            'downtimes': downtimes,
        }


    if request.method == "POST":
        data = json.loads(request.body)
        
        if 'sid' in data:
            downtime = DowntimeFromLine.objects.get(id=data['sid'])
            return JsonResponse({'downtime_text': downtime.downtime, 'station_text': downtime.station, 'category_text': downtime.category })
        
        else:
            downtime_object = DowntimeFromLine.objects.get(id=data['id'])

            if data['property'] == 'category':
                downtime_object.category = data['property_value']

            if data['property'] == 'station':
                downtime_object.station = data['property_value']

            if data['property'] == 'downtime_reason':
                downtime_object.downtime = data['property_value']

            if data['property'] == 'comment':
                downtime_object.comment = data['property_value']

            if data['property'] == 'split_downtime':
                downtime_object.end_t = data['property_value']
                downtime_object.save()

                new_downtime = DowntimeFromLine.objects.create(beginning_t=data['property_value'])

                if data['optional_property_value']:
                    if not data['optional_property_value'] == "...":
                        end_time = f"{data['optional_property_value'][10:20]} {data['optional_property_value'][0:8]}"
                        new_downtime.end_t = end_time
                        new_downtime.save()
                    else:
                        new_downtime.save()
        
            downtime_object.save()

            if data['property'] == 'split_downtime':
                return JsonResponse({'id': new_downtime.id})
            else:
                return JsonResponse({'okay': 'okay'})
        

    return render(request, 'operator_new.html', context)


@csrf_exempt
def check_for_downtime_auto(request):
    latest_piece_datetime = TbFp09CtSt135.objects.latest('productiontimestamp') # cas produkce posledniho kusu

    if (datetime.datetime.now() - latest_piece_datetime.productiontimestamp).total_seconds() > 35:
        downtime_beginning = latest_piece_datetime.productiontimestamp.replace(microsecond=0) + datetime.timedelta(seconds=5)
        downtime_from_line, created = DowntimeFromLine.objects.get_or_create(beginning_t=downtime_beginning)
        if created:
            stops_line_alarm_codes = list(StopLineAlarms.objects.values_list('alarmcode_id', flat=True)) # seznam alarmu ktere zastavuji linku
            actual_alarm = list(Tb_fp09_alarms.objects.filter(timestampalarm__lte=downtime_beginning - datetime.timedelta(seconds=5), alarmcode__in=stops_line_alarm_codes).values_list('timestampalarm', 'alarmcode').order_by('-timestampalarm'))[0] # co kdyz alarm zastavujici linku neni v StopLineAlarms?
            try:
                result = re.search('Alarms(.*)\[', actual_alarm[1]) # doplnit nulu pred 2digit code
                station_striped = result.group(1)
                s = ''.join(x for x in station_striped if x.isdigit())
                if len(s) < 3:
                    t = ''.join(x for x in station_striped if x.isalpha())
                    if len(s) == 2:
                        station_striped = t + '0' + s
                    if len(s) == 1:
                        station_striped = t + '00' + s
                downtime_from_line.station = station_striped
            except:
                pass
            finally:
                downtime_from_line.save()
    else:
        if DowntimeFromLine.objects.latest('beginning_t').end_t == None:
            downtime = DowntimeFromLine.objects.latest('beginning_t')
            downtime.end_t = latest_piece_datetime.productiontimestamp - datetime.timedelta(seconds=5)
            downtime.save()
        else:
            pass


    return HttpResponse('okay')
            

@csrf_exempt
def check_for_downtime(request):
    latest_piece_datetime = TbFp09CtSt135.objects.latest('productiontimestamp') # cas produkce posledniho kusu
    latest_downtime = DowntimeFromLine.objects.latest('beginning_t')

    response_dict = {}

    if (latest_downtime.end_t is None):
        response_dict['downtime'] = True
        downtime_beginning = latest_downtime.beginning_t
        response_dict['downtime_id'] = latest_downtime.id
        response_dict['beginning_t'] = downtime_beginning
        response_dict['station'] = latest_downtime.station
    else:
        response_dict['downtime'] = False
        response_dict['end_t'] = latest_downtime.end_t

    response_dict['last_produced_piece'] = latest_piece_datetime.productiontimestamp.replace(microsecond=0)

    return JsonResponse(response_dict)


@csrf_exempt
def add_historical_downtimes(request):

    data = json.loads(request.body)
    date_from = datetime.datetime.strptime(data['date'], "%Y-%m-%d").date()
    date_to = date_from + datetime.timedelta(days=1)
    downtimes = {}
    qs = DowntimeFromLine.objects.filter(beginning_t__gte=date_from, beginning_t__lte=date_to).order_by('beginning_t')
    for q in qs:
        downtimes[q.uid] = {}
        downtimes[q.uid]['station'] = q.station
        downtimes[q.uid]['category'] = q.category
        downtimes[q.uid]['downtime'] = q.downtime
        downtimes[q.uid]['comment'] = q.comment
        downtimes[q.uid]['beginning_t'] = str(q.beginning_t)
        downtimes[q.uid]['end_t'] = str(q.end_t)


    return JsonResponse(downtimes)


@csrf_exempt
def delete_downtime(request):

    uid = json.loads(request.body)['uid']
    DowntimeFromLine.objects.get(uid=uid).delete()

    return HttpResponse('okay')


@csrf_exempt
def get_sum_downtimes(request):

    data = json.loads(request.body)

    filters = {
        key: value
        for key, value in data['filters'].items() if value
    }

    return_data = round(DowntimeFromLine.objects.annotate(day=TruncDate('beginning_t')).filter(**filters).annotate(duration=F("end_t") - F("beginning_t")).values('day', 'duration').aggregate(sum_of_durations=Sum('duration'))['sum_of_durations'].total_seconds() / 60, 2) if DowntimeFromLine.objects.annotate(day=TruncDate('beginning_t')).filter(**filters).exists() else 0


    return JsonResponse(return_data, safe=False)


@csrf_exempt
def edit_database(request):
    shifts_per_day = 3

    if shifts_per_day == 3:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
        afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    if shifts_per_day == 2:
        morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        afternoon_shift_hours = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]


    if request.method == "GET":
        if 'beginning' in request.GET:
            shifts = request.GET['shift']
            if shifts_per_day == 3:
                beginning_dt = datetime.datetime.strptime(request.GET['beginning'], "%Y-%m-%d") - datetime.timedelta(hours=2)
                end_dt = datetime.datetime.strptime(request.GET['end'], "%Y-%m-%d") + datetime.timedelta(days=1) - datetime.timedelta(hours=2) 
                if shifts == 'All':
                    shifts = ['Morning', 'Afternoon', 'Night']
                else:
                    shifts = [shifts]

            if shifts_per_day == 2:
                beginning_dt = datetime.datetime.strptime(request.GET['beginning'], "%Y-%m-%d") + datetime.timedelta(hours=6)
                end_dt = datetime.datetime.strptime(request.GET['end'], "%Y-%m-%d") + datetime.timedelta(days=1, hours=6)
                if shifts == 'All':
                    shifts = ['Morning', 'Afternoon']
                else:
                    shifts = [shifts]

            return_data = []

            data = DowntimeFromLine.objects.filter(beginning_t__gte=beginning_dt, end_t__lte=end_dt).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=F("end_t") - F("beginning_t")).values('id', 'category', 'downtime', 'station', 'beginning_t', 'end_t', 'duration', 'comment').order_by('-beginning_t')

            for downtime in data:
                data_dict = {}
                data_dict['id'] = downtime['id']
                data_dict['category'] = downtime['category']
                data_dict['downtime'] = downtime['downtime']
                data_dict['station'] = downtime['station']
                data_dict['beginning_t'] = downtime['beginning_t']
                data_dict['end_t'] = downtime['end_t']
                data_dict['comment'] = downtime['comment']
                data_dict['duration'] = downtime['duration']

                return_data.append(data_dict)

            return JsonResponse({'data': return_data})

        data = DowntimeFromLine.objects.filter(beginning_t__gte=datetime.datetime.now().replace(hour=0, minute=0, second=0) - datetime.timedelta(hours=2)).annotate(duration=F("end_t") - F("beginning_t")).values('id', 'category', 'downtime', 'station', 'beginning_t', 'end_t', 'duration', 'comment').order_by('beginning_t')

    if request.method == "POST":
        
        data = json.loads(request.body)

        downtime = DowntimeFromLine.objects.get(id=data['id'])

        downtime.beginning_t = data['beginning_t']
        downtime.end_t = data['end_t']

        if "category" in data:
            downtime.category = data['category']

        downtime.save()
        
        return JsonResponse({'status': 'okay'})

    context = {
        'data': data,
        'categories': list(DowntimeFromLine.objects.exclude(category=None).exclude(category='').order_by('category').values_list('category', flat=True).distinct())
    }

    return render(request, 'edit_database.html', context)

@csrf_exempt
def get_fp09_downtime_fromline(request):

    morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
    afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    data = json.loads(request.body)

    shifts = data['shift']

    if 'count_of' in data: # tohle je pro top 10, 15, 20
        count_of = int(data['count_of']) # tohle je pro top 10, 15, 20
    else: # tohle je pro top 10, 15, 20
        count_of = 10 # tohle je pro top 10, 15, 20

    if shifts == 'All':
        shifts = ['Morning', 'Afternoon', 'Night']
    else:
        shifts = [shifts]

    range_to = datetime.date.today() - datetime.timedelta(days = 1)
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(range_to, time_to)
    range_from = range_to - datetime.timedelta(days = int(data['days']))

    if 'start_date' in data:
        datetime_from = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d") ## predpoklada predchozi den 22:00
        time_from = datetime.time(22,0,0)
        range_from = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)

    if 'end_date' in data:
        datetime_to = datetime.datetime.strptime(data['end_date'], "%Y-%m-%d") ## predpoklada den do 22:00
        time_to = datetime.time(22,0,0)
        range_to = datetime.datetime.combine(datetime_to, time_to)

    production_statistics = TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(day=Trunc('productiontime', 'day')).values('day').annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(total_parts=Count('dsid')).order_by('day')

    production_statistics_for_pareto = TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total_parts=Count('dsid'))['total_parts']

    downtime_statistics = list(DowntimeFromLine.objects.filter(beginning_t__gte=range_from, end_t__lt=range_to, downtime__gt='',downtime__isnull=False).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values_list('downtime', 'beginning_t', 'end_t'))
    downtime_statistics_time_dict = {}
    downtime_statistics_occur_dict = {}
    for downtime, beginning, end in downtime_statistics:
        time_delta = (end - beginning).total_seconds()
        if downtime not in downtime_statistics_time_dict:
            downtime_statistics_time_dict[downtime] = []
        downtime_statistics_time_dict[downtime].append(time_delta/60)
        if downtime not in downtime_statistics_occur_dict:
            downtime_statistics_occur_dict[downtime] = []
        downtime_statistics_occur_dict[downtime].append(1)
    sum_downtime_statistics_time_dict = {k:sum(v) for k,v in downtime_statistics_time_dict.items()}
    sum_downtime_statistics_occur_dict = {k:sum(v) for k,v in downtime_statistics_occur_dict.items()}
    sum_downtime_statistics_time_dict_top = dict(sorted(sum_downtime_statistics_time_dict.items(), key = itemgetter(1), reverse = True)[:count_of])
    results = []
    for key in sum_downtime_statistics_time_dict_top:
        results.append((key, sum_downtime_statistics_time_dict_top[key], sum_downtime_statistics_occur_dict[key]))

    if data['type'] == 'individual_relative_pareto':

        results_data = [(key, val0, val1 / production_statistics_for_pareto, val1) if val0 is not None else (key, 0, 0) for (key, val0, val1) in results]

        results_data.sort(key = lambda tup: tup[2], reverse=True)

        data_data = [(key, val1) for (key, val0, val1, val2) in results_data]
        tooltips_data = [f"Četnost: {val2}|Trvání: {round(val0)}" for (key, val0, val1, val2) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }

    if data['type'] == 'individual_relative_line':
        downtimes = []
        production_statistics_daily = list(TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(day=Trunc('productiontime', 'day')).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('day').annotate(total_parts=Count('dsid')).order_by('day').values_list('total_parts', flat=True))
        range_to_day = range_from.date() + datetime.timedelta(days = 1)
        range_to_datetime = datetime.datetime(range_to_day.year, range_to_day.month, range_to_day.day)
        range_from_datetime = range_from
        while range_to >= range_to_datetime:
            day = range_from_datetime.date()
            downtime_statistics_daily = list(DowntimeFromLine.objects.filter(beginning_t__gte=range_from_datetime, end_t__lt=range_to_datetime, downtime__gt='',downtime__isnull=False).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values_list('downtime', 'beginning_t', 'end_t'))
            range_from_datetime = range_to_datetime
            range_to_datetime += datetime.timedelta(days=1)
            downtime_statistics_time_dict = {}
            downtime_statistics_occur_dict = {}
            for downtime, beginning, end in downtime_statistics_daily:
                time_delta = (end - beginning).total_seconds()
                if downtime not in downtime_statistics_time_dict:
                    downtime_statistics_time_dict[downtime] = []
                downtime_statistics_time_dict[downtime].append(time_delta/60)
                if downtime not in downtime_statistics_occur_dict:
                    downtime_statistics_occur_dict[downtime] = []
                downtime_statistics_occur_dict[downtime].append(1)
            sum_downtime_statistics_time_dict = {k:sum(v) for k,v in downtime_statistics_time_dict.items()}
            sum_downtime_statistics_occur_dict = {k:sum(v) for k,v in downtime_statistics_occur_dict.items()}
            for key in sum_downtime_statistics_time_dict:
                if key in sum_downtime_statistics_time_dict_top:
                    downtimes.append((day, key, sum_downtime_statistics_time_dict[key], sum_downtime_statistics_occur_dict[key]))

        downtime_statistics_daily = list(DowntimeFromLine.objects.filter(beginning_t__gte=range_from_datetime, end_t__lt=range_to, downtime__gt='',downtime__isnull=False).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values_list('downtime', 'beginning_t', 'end_t'))
        downtime_statistics_time_dict = {}
        downtime_statistics_occur_dict = {}
        for downtime, beginning, end in downtime_statistics_daily:
            time_delta = (end - beginning).total_seconds()
            if downtime not in downtime_statistics_time_dict:
                downtime_statistics_time_dict[downtime] = []
            downtime_statistics_time_dict[downtime].append(time_delta/60)
            if downtime not in downtime_statistics_occur_dict:
                downtime_statistics_occur_dict[downtime] = []
            downtime_statistics_occur_dict[downtime].append(1)
        sum_downtime_statistics_time_dict = {k:sum(v) for k,v in downtime_statistics_time_dict.items()}
        sum_downtime_statistics_occur_dict = {k:sum(v) for k,v in downtime_statistics_occur_dict.items()}
        day = range_from_datetime.date()
        for key in sum_downtime_statistics_time_dict:
            if key in sum_downtime_statistics_time_dict_top:
                downtimes.append((day, key, sum_downtime_statistics_time_dict[key], sum_downtime_statistics_occur_dict[key]))
        downtimes_top = [*sum_downtime_statistics_time_dict_top]
        days = set()
        datasets = []
        for dict_data in list(production_statistics):
            days.add(dict_data['day'].date())
        alarm_reasons = []
        days = sorted(days)
 
        for downtime_top in downtimes_top:
            dataset = {}
            dataset['label'] = downtime_top

            dataset['data'] = [(dt, duration, alarm_count) for (dt, code, duration, alarm_count) in downtimes if (downtime_top == code and dt in days)]

            dataset['borderColor'] = 'rgb(255,255,255)'

            if len(days) > len(dataset['data']):
                days_in_alarms = (dt for (dt, duration, alarm_count) in dataset['data'])
                missing_days = set(days) - set(days_in_alarms)
                for missing_day in missing_days:
                    dataset['data'].append((missing_day, 0, 0, 0))
                
                dataset['data'].sort(key = lambda tup: tup[0])
            for index, day in enumerate(days):
                dataset['data'][index] = (dataset['data'][index][0], dataset['data'][index][1], dataset['data'][index][2] / production_statistics_daily[index], dataset['data'][index][2])
            dataset['tooltips'] = [f"Četnost: {raw_count}|Trvání: {round(duration)}" if duration is not None else (duration, alarm_count) for (dt, duration, alarm_count, raw_count) in dataset['data']]

            dataset['data'] = [alarm_count if alarm_count is not None else 0 for (dt, duration, alarm_count, raw_count) in dataset['data']]

            datasets.append(dataset)
            
        return_data = {
            'days': data['days'],
            'days_in_range': days,
            'datasets': datasets,
        }

    
    if data['type'] == 'individual_pareto':

        results_data = [(key, val0, val1) if val0 is not None else (key, 0, 0) for (key, val0, val1) in results]

        results_data.sort(key = lambda tup: tup[1], reverse=True)

        data_data = [(key, val0) for (key, val0, val1) in results_data]
        tooltips_data = [f"Četnost: {val1}|Trvání: {round(val0)}" for (key, val0, val1) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }

    if data['type'] == 'individual_line':
        downtimes = []
        production_statistics_daily = list(TbFp09Qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to).filter(Q(formerstation="130") | (Q(formerstation="135") & Q(partstatus__in=["89", "105"]))).values('dsid', 'partstatus', 'productiontime', 'formerstation').annotate(day=Trunc('productiontime', 'day')).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('day').annotate(total_parts=Count('dsid')).order_by('day').values_list('total_parts', flat=True))
        range_to_day = range_from.date() + datetime.timedelta(days = 1)
        range_to_datetime = datetime.datetime(range_to_day.year, range_to_day.month, range_to_day.day)
        range_from_datetime = range_from
        while range_to >= range_to_datetime:
            day = range_from_datetime.date()
            downtime_statistics_daily = list(DowntimeFromLine.objects.filter(beginning_t__gte=range_from_datetime, end_t__lt=range_to_datetime, downtime__gt='',downtime__isnull=False).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values_list('downtime', 'beginning_t', 'end_t'))
            range_from_datetime = range_to_datetime
            range_to_datetime += datetime.timedelta(days=1)
            downtime_statistics_time_dict = {}
            downtime_statistics_occur_dict = {}
            for downtime, beginning, end in downtime_statistics_daily:
                time_delta = (end - beginning).total_seconds()
                if downtime not in downtime_statistics_time_dict:
                    downtime_statistics_time_dict[downtime] = []
                downtime_statistics_time_dict[downtime].append(time_delta/60)
                if downtime not in downtime_statistics_occur_dict:
                    downtime_statistics_occur_dict[downtime] = []
                downtime_statistics_occur_dict[downtime].append(1)
            sum_downtime_statistics_time_dict = {k:sum(v) for k,v in downtime_statistics_time_dict.items()}
            sum_downtime_statistics_occur_dict = {k:sum(v) for k,v in downtime_statistics_occur_dict.items()}
            for key in sum_downtime_statistics_time_dict:
                if key in sum_downtime_statistics_time_dict_top:
                    downtimes.append((day, key, sum_downtime_statistics_time_dict[key], sum_downtime_statistics_occur_dict[key]))

        downtime_statistics_daily = list(DowntimeFromLine.objects.filter(beginning_t__gte=range_from_datetime, end_t__lt=range_to, downtime__gt='',downtime__isnull=False).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values_list('downtime', 'beginning_t', 'end_t'))
        downtime_statistics_time_dict = {}
        downtime_statistics_occur_dict = {}
        for downtime, beginning, end in downtime_statistics_daily:
            time_delta = (end - beginning).total_seconds()
            if downtime not in downtime_statistics_time_dict:
                downtime_statistics_time_dict[downtime] = []
            downtime_statistics_time_dict[downtime].append(time_delta/60)
            if downtime not in downtime_statistics_occur_dict:
                downtime_statistics_occur_dict[downtime] = []
            downtime_statistics_occur_dict[downtime].append(1)
        sum_downtime_statistics_time_dict = {k:sum(v) for k,v in downtime_statistics_time_dict.items()}
        sum_downtime_statistics_occur_dict = {k:sum(v) for k,v in downtime_statistics_occur_dict.items()}
        day = range_from_datetime.date()
        for key in sum_downtime_statistics_time_dict:
            if key in sum_downtime_statistics_time_dict_top:
                downtimes.append((day, key, sum_downtime_statistics_time_dict[key], sum_downtime_statistics_occur_dict[key]))
        downtimes_top = [*sum_downtime_statistics_time_dict_top]

        days = set()
        datasets = []

        for dict_data in list(production_statistics):
            days.add(dict_data['day'].date())

        days = sorted(days)
            
        for downtime_top in downtimes_top:
            dataset = {}
            dataset['label'] = downtime_top

            dataset['data'] = [(dt, duration, alarm_count) for (dt, code, duration, alarm_count) in downtimes if (downtime_top == code and dt in days)]

            dataset['borderColor'] = 'rgb(255,255,255)'

            if len(days) > len(dataset['data']):
                days_in_alarms = (dt for (dt, duration, alarm_count) in dataset['data'])
                missing_days = set(days) - set(days_in_alarms)
                for missing_day in missing_days:
                    dataset['data'].append((missing_day, 0, 0))
                
                dataset['data'].sort(key = lambda tup: tup[0])
            
            dataset['tooltips'] = [f"Četnost: {alarm_count}|Trvání: {round(duration)}" if duration is not None else (duration, alarm_count) for (dt, duration, alarm_count) in dataset['data']]

            dataset['data'] = [(duration) if duration is not None else duration for (dt, duration, alarm_count) in dataset['data']]

            datasets.append(dataset)
    
        return_data = {
            'days': data['days'],
            'days_in_range': days,
            'datasets': datasets,
        }

    if data['type'] == 'group_pareto':

        results = {}

        groups = FP09_alarm_description.objects.all().values_list('group', flat=True).exclude(group='').distinct('group')

        for group in groups:
            group_alarm_codes = list(FP09_alarm_description.objects.filter(group=group).values_list('code', flat=True))
            results[group] = (
                Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total=Sum('alarmtime'))['total'],
                Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(total=Count('alarmtime'))['total']
            )

        results_data = [(key, value[0] / 60_000, value[1]) if value[0] is not None else (key, 0, 0) for (key, value) in results.items()]

        results_data.sort(key = lambda tup: tup[1], reverse=True)

        data_data = [(key, val0) for (key, val0, val1) in results_data]
        tooltips_data = [f"Četnost: {val1}|Trvání: {round(val0)}" for (key, val0, val1) in results_data]

        return_data = {
            'days': data['days'],
            'data': data_data,
            'tooltips': tooltips_data,
        }


    if data['type'] == 'group_line':
        days = set()

        for dict_data in list(production_statistics):
            days.add(dict_data['day'])

        days = sorted(days)

        datasets = []
        
        groups = FP09_alarm_description.objects.all().values_list('group', flat=True).exclude(group='').distinct('group')

        results = {}

        for group in groups:
            group_alarm_codes = list(FP09_alarm_description.objects.filter(group=group).values_list('code', flat=True))
            results[group] = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=group_alarm_codes).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(day=Trunc('timestampalarm', 'day')).order_by('day').values('day').annotate(duration=Sum('alarmtime'), alarm_count=Count('alarmtime')).values_list('day', 'duration', 'alarm_count'))

            group_alarm_dates = [tup[0] for tup in results[group]]

            for day in days:
                if not day in group_alarm_dates:
                    results[group].append((day, 0, 0))

            results[group].sort(key = lambda tup: tup[0])

            results[group] = [(to_minutes(tup[1]), tup[2]) for tup in results[group] if tup[0] in days]                

        
        for group, values in results.items():
            dataset = {}
            dataset['label'] = group
            dataset['data'] = [num[0] for num in values]
            dataset['tooltips'] = [f"Četnost: {num[1]}|Trvání: {round(num[0])}" for num in values]
            dataset['borderColor'] = 'rgb(255,255,255)'
            datasets.append(dataset)

        return_data = {
            'days': data['days'],
            'days_in_range': [day.date() for day in days],
            'datasets': datasets,
        }
    
    return JsonResponse(return_data)

@csrf_exempt
def downtime_fromline(request):

    colors = list(FP09_alarm_description.objects.all().values('description', 'color_code'))
    group_colors = list(FP09_alarm_description.objects.all().values('group', 'color_code'))

    color_codes = {}

    for item in colors:
        color_codes[item['description']] = item['color_code']
        color_codes[item['description'][:25]] = item['color_code']

    for item in group_colors:
        color_codes[item['group']] = item['color_code']
        color_codes[item['group'][:25]] = item['color_code']

    context = {
        'colors': color_codes,
    }

    return render(request, 'fp09_downtime_fromline.html', context)
    

@csrf_exempt
def fp09_downtime_trends_details(request):

    parameters = json.loads(request.body)

    MORNING_SHIFT_HOURS = [6, 7, 8, 9, 10, 11, 12, 13]
    AFTERNOON_SHIFT_HOURS = [14, 15, 16, 17, 18, 19, 20, 21]

    shifts = parameters['shifts'] or ['Morning', 'Afternoon', 'Night']

    categories = {
        'technical': 'Technical downtime / technický prostoj'
    }

    return_data = {}

    downtime_details_reference = list(DowntimeFromLine.objects.values('downtime', 'beginning_t', 'end_t').filter(beginning_t__gte=parameters['reference_timestamp_from'], beginning_t__lt=parameters['reference_timestamp_to'], category=categories[parameters['category']]).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=MORNING_SHIFT_HOURS, then=Value('Morning')), When(hour_start__in=AFTERNOON_SHIFT_HOURS, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=Epoch(F("end_t") - F("beginning_t"))).values('downtime', 'duration').order_by('duration'))

    downtime_details_actual = list(DowntimeFromLine.objects.values('downtime', 'beginning_t', 'end_t').filter(beginning_t__gte=parameters['actual_timestamp_from'], beginning_t__lt=parameters['actual_timestamp_to'], category=categories[parameters['category']]).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=MORNING_SHIFT_HOURS, then=Value('Morning')), When(hour_start__in=AFTERNOON_SHIFT_HOURS, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).annotate(duration=Epoch(F("end_t") - F("beginning_t"))).values('downtime', 'duration').order_by('duration'))

    for data_dict in downtime_details_reference:
        return_data[data_dict['downtime']] = [data_dict['duration'], 0]

    for data_dict in downtime_details_actual:
        for downtime, duration in data_dict.items():
            return_data[downtime][1] = duration
        else:
            return_data[downtime] = [0, duration]

    return JsonResponse({'okay': 'okay'})


def get_data_downtime_trends(interval_start, interval_end, button, shift):
    shifts_per_day = 3

    if shifts_per_day == 3:
        time_from = datetime.time(22,0,0)
        time_to = datetime.time(22,0,0)
        interval_start = datetime.datetime.combine((interval_start - datetime.timedelta(days=1)), time_from)
        interval_end = datetime.datetime.combine(interval_end, time_to)

    if shifts_per_day == 2:
        time_from = datetime.time(6, 0, 0)
        time_to = datetime.time(6, 0, 0)
        interval_start = datetime.datetime.combine(interval_start, time_from)
        interval_end = datetime.datetime.combine(interval_end + datetime.timedelta(days = 1), time_to)

    days_in_range = []
    days = 0
    datetime_iteration = interval_start

    while datetime_iteration.date() <= interval_end.date():
        days_in_range.append(datetime_iteration.date())
        datetime_iteration = datetime_iteration + datetime.timedelta(days=1)
        days += 1

    interval_values = {}

    if shifts_per_day == 3:
        if shift == 'All':
            shift = ['Morning', 'Afternoon', 'Night']
        else:
            shift = [shift]

    if shifts_per_day == 2:
        if shift == 'All':
            shift = ['Morning', 'Afternoon']
        else:
            shift = [shift]
    
    if shifts_per_day == 3:
        MORNING_SHIFT_HOURS = [6, 7, 8, 9, 10, 11, 12, 13]
        AFTERNOON_SHIFT_HOURS = [14, 15, 16, 17, 18, 19, 20, 21]

    if shifts_per_day == 2:
        MORNING_SHIFT_HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        AFTERNOON_SHIFT_HOURS = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]


    if button == "All / Vše":
        categories = list(Downtime.objects.values_list('category', flat=True).distinct('category'))
        for category in categories:
            interval_values[category] = []
        for category in categories:
            i = 0
            for day in days_in_range:
                i += 1
                datetime_from = datetime.datetime.combine(day, datetime.datetime.min.time())
                datetime_to = datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.datetime.min.time())
                if i == 1:
                    datetime_from = datetime_from + datetime.timedelta(hours=22)
                if i == len(days_in_range):
                    datetime_to = datetime_to - datetime.timedelta(hours=2)
                interval_value = list(DowntimeFromLine.objects.filter(category=category, beginning_t__gte=datetime_from, end_t__lt=datetime_to).annotate(duration=Epoch(F("end_t") - F("beginning_t"))).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=MORNING_SHIFT_HOURS, then=Value('Morning')), When(hour_start__in=AFTERNOON_SHIFT_HOURS, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shift).values('category').annotate(total_duration=Sum('duration'), total_quantity=Count('duration')).values_list('total_duration', 'total_quantity'))
                if len(interval_value) > 0:    
                    interval_values[category].append((day, interval_value[0][0] / 60, interval_value[0][1]))
                else:
                    interval_values[category].append((day, 0, 0))
        return days, days_in_range, interval_values
    else:
        downtimes = list(DowntimeFromLine.objects.filter(category=button, beginning_t__gte=interval_start, end_t__lt=interval_end).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=MORNING_SHIFT_HOURS, then=Value('Morning')), When(hour_start__in=AFTERNOON_SHIFT_HOURS, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shift).values_list('downtime', flat=True).distinct('downtime'))
        for downtime in downtimes:
            interval_values[downtime] = []
        for downtime in downtimes:
            i = 0
            for day in days_in_range:
                i += 1
                datetime_from = datetime.datetime.combine(day, datetime.datetime.min.time())
                datetime_to = datetime.datetime.combine(day + datetime.timedelta(days=1), datetime.datetime.min.time())
                if i == 1:
                    datetime_from = datetime_from + datetime.timedelta(hours=22)
                if i == len(days_in_range):
                    datetime_to = datetime_to - datetime.timedelta(hours=2)
                interval_value = list(DowntimeFromLine.objects.filter(category=button, downtime=downtime, beginning_t__gte=datetime_from, end_t__lt=datetime_to).values('beginning_t').annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=MORNING_SHIFT_HOURS, then=Value('Morning')), When(hour_start__in=AFTERNOON_SHIFT_HOURS, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shift).annotate(duration=Epoch(F("end_t") - F("beginning_t"))).values('category').annotate(total_duration=Sum('duration'), total_quantity=Count('duration')).values_list('total_duration', 'total_quantity'))
                if len(interval_value) > 0:    
                    interval_values[downtime].append((day, interval_value[0][0] / 60, interval_value[0][1]))
                else:
                    interval_values[downtime].append((day, 0, 0))
        return days, days_in_range, interval_values

def setColor(category, used_colors):
    if category == 'Changeover / Přestavba':
        color = 'rgb(55, 76, 128)'
    elif category == 'Input components + packaging / Vstupní komponenty + balení':
        color = 'rgb(122, 81, 149)'
    elif category == 'Logistic / Logistika':
        color = 'rgb(188, 80, 144)'
    elif category == 'Organization / Organizace':
        color = 'rgb(239, 86, 117)'
    elif category == 'Repair, maintenance / Oprava, údržba':
        color = 'rgb(255, 118, 74)'
    elif category == 'Technical downtime / technický prostoj':
        color = 'rgb(255, 166, 0)'
    else:
        if category in used_colors:
            color = used_colors[category]
        else:
            r = random.randint(0,255)
            g = random.randint(0,255)
            b = random.randint(0,255)
            color = f'rgb({r}, {g}, {b})'
            used_colors[category] = color
    return color, used_colors


def split_downtimes(request):
    downtimes_ended_in_last_hour = DowntimeFromLine.objects.filter(beginning_t__gte='2022-09-01', end_t__isnull=False)

    for downtime in downtimes_ended_in_last_hour:
        downtime_shift_end = get_shift_end(downtime)
        if downtime.end_t > downtime_shift_end:
            original_downtime_end = downtime.end_t
            downtime.end_t = downtime_shift_end
            downtime.save()

            new_downtime = DowntimeFromLine.objects.create(
                station = downtime.station,
                category = downtime.category,
                downtime = downtime.downtime,
                beginning_t = downtime_shift_end,
                end_t = original_downtime_end,
                comment = downtime.comment,
                uploaded_to_xlsx = False,
                uid = downtime.uid,
            )

    return HttpResponse('okay')


def get_shift_end(downtime):
    shifts_per_day = 3

    if shifts_per_day == 3:
        if 6 <= downtime.beginning_t.hour < 14:
            return downtime.beginning_t.replace(hour=14, minute=0, second=0)
        if 14 <= downtime.beginning_t.hour < 22:
            return downtime.beginning_t.replace(hour=22, minute=0, second=0)
        if downtime.beginning_t.hour >= 22:
            try:
                return downtime.beginning_t.replace(day=downtime.beginning_t.day + 1, hour=6, minute=0, second=0)
            except ValueError:
                if downtime.beginning_t.month < 12:
                    return downtime.beginning_t.replace(day=1, month=downtime.beginning_t.month + 1, hour=6, minute=0, second=0)
                else:
                    return downtime.beginning_t.replace(day=1, month=1, year=downtime.beginning_t.year + 1, hour=6, minute=0, second=0)
        if downtime.beginning_t.hour < 6:
            return downtime.beginning_t.replace(hour=6, minute=0, second=0)

    if shifts_per_day == 2:
        if 6 <= downtime.beginning_t.hour < 18:
            return downtime.beginning_t.replace(hour=18, minute=0, second=0)
        if downtime.beginning_t.hour >= 18:
            return downtime.beginning_t.replace(hour=6, minute=0, second=0) + datetime.timedelta(days = 1)
        if downtime.beginning_t.hour < 6:
            return downtime.beginning_t.replace(hour=6, minute=0, second=0)

@csrf_exempt
def downtime_editor(request):

    if request.method == "GET":
        all_data = Downtime.objects.all().order_by('category')

        context = {
            'data': all_data,
            'downtime_categories': Downtime.objects.all().values_list('category', flat=True).distinct('category'),
        }


    if request.method == "POST":
        request_data = json.loads(request.body)

        if 'id' in request_data:
            downtime_object = Downtime.objects.get(id=request_data['id'])

            if request_data['name'] == '':
                downtime_object.delete()
                return JsonResponse({'okay': 'okay'})
            
            downtime_object.category = request_data['category']
            downtime_object.station = request_data['station']
            downtime_object.name = request_data['name']
            downtime_object.save()
        
        else:
            downtime_object = Downtime.objects.create(category=request_data['category'], station=request_data['station'], name=request_data['name'])

        return JsonResponse({'okay': 'okay'})


    return render(request, 'downtime_editor.html', context)


@csrf_exempt
def get_fp09_alarms_sum(request):
    parameters = json.loads(request.body)

    morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
    afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    shifts = parameters['shift']
    stops_line = parameters['stops_line'] 
    does_not_stop_line = parameters['does_not_stop_line'] 
    informs_line = parameters['informs_line'] 

    if shifts == 'All':
        shifts = ['Morning', 'Afternoon', 'Night']
    else:
        shifts = [shifts]

    range_to = datetime.date.today() - datetime.timedelta(days = 1)
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(range_to, time_to)
    range_from = range_to - datetime.timedelta(days = int(parameters['days']))

    datetime_from = datetime.datetime.strptime(parameters['start_date'][:10], "%Y-%m-%d")
    time_from = datetime.time(22,0,0)
    range_from = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)

    datetime_to = datetime.datetime.strptime(parameters['end_date'][:10], "%Y-%m-%d")
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(datetime_to, time_to)

    actual_alarms = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to).values_list('alarmcode', flat=True)

    stops_line_alarms = list(Tb_fp09_alarmstext.objects.filter(Q(alarmtype=1) | Q(alarmtype__isnull=True)).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True))
    slows_line_alarms = list(Tb_fp09_alarmstext.objects.filter(alarmtype=2).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True)) 
    informs_line_alarms =  list(Tb_fp09_alarmstext.objects.filter(alarmtype=3).filter(alarmcode__in=actual_alarms).values_list('alarmcode_id', flat=True)) 

    alarms_included = [] 

    if stops_line: 
        alarms_included.extend(stops_line_alarms) 

    if does_not_stop_line: 
        alarms_included.extend(slows_line_alarms) 

    if informs_line: 
        alarms_included.extend(informs_line_alarms) 

    # downtime_statistics = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarms_included).values('timestampalarm', 'alarmcode').annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).values('alarmcode').annotate(duration=Sum('alarmtime')).annotate(alarm_count=Count('alarmtime')).exclude(duration__isnull=True).order_by('-alarm_count').values_list('alarmcode', 'duration', 'alarm_count'))

    downtimes_duration = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarms_included).annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(duration_sum=Sum('alarmtime'))

    downtimes_count = Tb_fp09_alarms.objects.filter(timestampalarm__gte=range_from, timestampalarm__lte=range_to, alarmcode__in=alarms_included).annotate(hour_start=ExtractHour('timestampalarm')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).aggregate(alarms_count=Count('hour_start'))

    return JsonResponse({'duration': round(downtimes_duration['duration_sum'] / 1000 / 60), 'count': downtimes_count['alarms_count']})


@csrf_exempt
def get_fp09_produced_partnumber(request):
    parameters = json.loads(request.body)

    morning_shift_hours = [6, 7, 8, 9, 10, 11, 12, 13]
    afternoon_shift_hours = [14, 15, 16, 17, 18, 19, 20, 21]

    shifts = parameters['shift']

    if shifts == 'All':
        shifts = ['Morning', 'Afternoon', 'Night']
    else:
        shifts = [shifts]

    range_to = datetime.date.today() - datetime.timedelta(days = 1)
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(range_to, time_to)
    range_from = range_to - datetime.timedelta(days = int(parameters['days']))

    datetime_from = datetime.datetime.strptime(parameters['start_date'][:10], "%Y-%m-%d")
    time_from = datetime.time(22,0,0)
    range_from = datetime.datetime.combine((datetime_from - datetime.timedelta(days=1)), time_from)

    datetime_to = datetime.datetime.strptime(parameters['end_date'][:10], "%Y-%m-%d")
    time_to = datetime.time(22,0,0)
    range_to = datetime.datetime.combine(datetime_to, time_to)

    produced_parts = list(Tb_fp09_qd.objects.filter(productiontime__gte=range_from, productiontime__lte=range_to, partstatus__in=['25', '41', '89', '105']).annotate(hour_start=ExtractHour('productiontime')).annotate(shift=Case(When(hour_start__in=morning_shift_hours, then=Value('Morning')), When(hour_start__in=afternoon_shift_hours, then=Value('Afternoon')), default=Value('Night'), output_field=CharField())).filter(shift__in=shifts).exclude(typenumber='').values('typenumber').annotate(produced_pcs=Count('typenumber')).order_by('produced_pcs').values_list('typenumber', 'produced_pcs'))

    parts_with_details = [(item[0], *get_type_details(item[0]), item[1]) for item in produced_parts]
    
    return JsonResponse({'data': parts_with_details})


@csrf_exempt
def type_details(request):

    if request.method == "GET":
        context = {
            'types': TypeDetails.objects.all()
        }
    
    if request.method == "POST":
        data = json.loads(request.body)
        for table_row in data['table_data']:
            partnumber, created = TypeDetails.objects.get_or_create(partnumber=table_row[0])
            partnumber.konstrukcni_varianta = table_row[1]
            partnumber.typ_krouzku = table_row[2]
            partnumber.typ_zavitu = table_row[3]
            partnumber.barva = table_row[4]
            partnumber.save()

    return render(request, 'type_details.html', context)


def get_type_details(partnumber):
    try:
        part = TypeDetails.objects.get(partnumber=partnumber)
        return part.konstrukcni_varianta, part.typ_krouzku, part.typ_zavitu, part.barva
    except:
        return "", "", "", ""


@csrf_exempt
def counter(request):
    if request.method == "GET":
        return render(request, 'counter.html', {})
    if request.method == "POST":
        Counter.objects.create(info = json.loads(request.body)['info'])
        return JsonResponse({'resp': 'okay'})


@csrf_exempt
def performance_report(request):
    
    if request.method == "GET":

        return render(request, 'fp09_performance_report.html', {})

    if request.method == "POST":
    
        charts_data = {
            'cycle_time': [],
            'weekly_oee': [],
            'weekly_rq': [],
            'weekly_pareto_time_loss': [],
            'losses': [],
            'average_shift_output': [],
        }

        request_data = json.loads(request.body)
        date_from = string_to_date(request_data['date_from'])
        date_to = string_to_date(request_data['date_to'])
        shifts = request_data['shifts']

        x_axis = dates_to_x_axis(date_from, date_to)

        charts_data['cycleTime'] = get_chart_data('cycle_time', date_from, date_to, x_axis, shifts)
        charts_data['averageShiftOutput'] = get_chart_data('average_shift_output', date_from, date_to, x_axis, shifts)
        charts_data['OEE'] = get_chart_data('oee', date_from, date_to, x_axis, shifts)
        charts_data['RQ'] = get_chart_data('rq', date_from, date_to, x_axis, shifts)
        charts_data['losses'] = get_chart_data('losses', date_from, date_to, x_axis, shifts)
        
        return JsonResponse({'xAxis': x_axis, 'chartsData': charts_data})


def get_chart_data(chart_name, date_from, date_to, x_axis, shifts):

    if chart_name == 'cycle_time':
        return {
            'targetCT' : [4.1 for _ in x_axis],
            'CT': get_average_cycle_time(date_from, date_to, shifts),
            }

    if chart_name == 'average_shift_output':
        return {
            'targetPCS': [4400 for _ in x_axis],
            'PCS': get_average_shift_output(date_from, date_to, shifts),
        }

    if chart_name == 'oee':
        return {
            'targetOEE': [70 for _ in x_axis],
            'OEE': get_oee(date_from, date_to, shifts),
        }

    if chart_name == 'rq':
        return {
            'targetRQ': [99 for _ in x_axis],
            'RQ': get_rq(date_from, date_to, shifts),
        }

    if chart_name == 'losses':
        losses = {
            'quality': [],
            'logistics': [],
            'changeover': [],
            'technical': [],
            'organization': [],
            'paint': [],
            'performance': []
        }
        
        query_database(losses, 'quality', date_from, date_to, shifts),
        query_database(losses, 'logistics', date_from, date_to, shifts),
        query_database(losses, 'changeover', date_from, date_to, shifts)
        query_database(losses, 'technical', date_from, date_to, shifts),
        query_database(losses, 'organization', date_from, date_to, shifts),
        query_database(losses, 'paint', date_from, date_to, shifts),
        query_database(losses, 'performance', date_from, date_to, shifts),

        return losses


def get_rq(date_from, date_to, shifts):
    average_rq = []

    if date_to - date_from < datetime.timedelta(days=14):
        with connections['jirkal_0003_fp'].cursor() as cursor:
            while date_from <= date_to:
                cursor.execute(f'WITH Shift_Statistics AS (SELECT OK_Total,  NOK_ST030L + NOK_ST030R + NOK_ST000L + NOK_ST000R + NOK_ST010L + NOK_ST010R + NOK_ST040L + NOK_ST040R + NOK_ST050L + NOK_ST050R + NOK_ST060L + NOK_ST060R + NOK_ST070L + NOK_ST070R + NOK_ST085L + NOK_ST085R + NOK_ST090L + NOK_ST090R + NOK_ST105L + NOK_ST105R + NOK_ST106L + NOK_ST106R + NOK_ST130 + NOK_ST135 + NOK_WIDTH + NOK_ST150 + NOK_ST160 + NOK_ST108L + NOK_ST108R AS NOK_total, ShiftDate, CASE WHEN CONVERT(TIME, ShiftDate) >= \'06:00\' AND CONVERT(TIME, ShiftDate) < \'18:00\' THEN \'R\' ELSE \'O\' END AS Shift FROM TB_FP09_ShiftCounters_Statistic) SELECT SUM(OK_Total), SUM(NOK_Total), CONVERT(DATE, ShiftDate) AS "Shift Date" FROM Shift_Statistics WHERE Shift IN ({shifts_to_string(shifts)}) AND CONVERT(DATE, ShiftDate) = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND OK_Total > 0 GROUP BY CONVERT(DATE, ShiftDate)')

                results = cursor.fetchone()

                if results:
                    average_rq.append((1 - (results[1] / (results[0] + results[1]))) * 100)
                else:
                    average_rq.append(None)

                date_from += datetime.timedelta(days=1)
    else:
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))
        first_week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
        last_week_end = date_to + datetime.timedelta(days = 6 - date_to.weekday())

        with connections['jirkal_0003_fp'].cursor() as cursor:
            cursor.execute(f'WITH Shift_Statistics AS (SELECT OK_Total,  NOK_ST030L + NOK_ST030R + NOK_ST000L + NOK_ST000R + NOK_ST010L + NOK_ST010R + NOK_ST040L + NOK_ST040R + NOK_ST050L + NOK_ST050R + NOK_ST060L + NOK_ST060R + NOK_ST070L + NOK_ST070R + NOK_ST085L + NOK_ST085R + NOK_ST090L + NOK_ST090R + NOK_ST105L + NOK_ST105R + NOK_ST106L + NOK_ST106R + NOK_ST130 + NOK_ST135 + NOK_WIDTH + NOK_ST150 + NOK_ST160 + NOK_ST108L + NOK_ST108R AS NOK_total, ShiftDate, CASE WHEN CONVERT(TIME, ShiftDate) >= \'06:00\' AND CONVERT(TIME, ShiftDate) < \'18:00\' THEN \'R\' ELSE \'O\' END AS Shift FROM TB_FP09_ShiftCounters_Statistic) SELECT SUM(OK_Total), SUM(NOK_Total), DATEPART(ISO_WEEK, ShiftDate) FROM Shift_Statistics WHERE ShiftDate >= \'{datetime.datetime.strftime(first_week_start, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(last_week_end, "%Y-%m-%d")}\' GROUP BY DATEPART(ISO_WEEK, ShiftDate)')
                    
            results = cursor.fetchall()

            results_weeks = {week: (ok_parts/(ok_parts + nok_parts) * 100) if (ok_parts + nok_parts > 0) else 0 for (ok_parts, nok_parts, week) in results}

            weeks = range(first_week, last_week + 1)

            for week in weeks:
                if not week in results_weeks:
                    average_rq.append(0)
                else:
                    average_rq.append(results_weeks[week])

    return average_rq


def get_oee(date_from, date_to, shifts):
    average_oee = []

    if date_to - date_from < datetime.timedelta(days=14):
        with connections['jirkal_0003_fp'].cursor() as cursor:
            while date_from <= date_to:
                cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\') AND ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days = 1), "%Y-%m-%d")}\'), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced) / 7024.0, DateOfShift FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DateOfShift = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND PartsProduced > 500 GROUP BY DateOfShift')

                results = cursor.fetchone()

                if results:
                    average_oee.append(results[0] * 100)
                else:
                    average_oee.append(None)


                date_from += datetime.timedelta(days=1)

    else:
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))
        first_week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
        last_week_end = date_to + datetime.timedelta(days = 6 - date_to.weekday())

        with connections['jirkal_0003_fp'].cursor() as cursor:
            cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\') AND ProductionTime >= \'{datetime.datetime.strftime(first_week_start - datetime.timedelta(days = 1), "%Y-%m-%d")}\'), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced) / 7024.0, DATEPART(ISO_WEEK, "DateOfShift") FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DateOfShift >= \'{datetime.datetime.strftime(first_week_start, "%Y-%m-%d")}\' AND DateOfShift <= \'{datetime.datetime.strftime(last_week_end, "%Y-%m-%d")}\' AND PartsProduced > 500 GROUP BY DATEPART(ISO_WEEK, "DateOfShift")')
                    
            results = cursor.fetchall()

            results_weeks = {week:result for (result, week) in results}

            weeks = range(first_week, last_week + 1)

            for week in weeks:
                if not week in results_weeks:
                    average_oee.append(0)
                else:
                    average_oee.append(results_weeks[week] * 100)

    return average_oee


def get_average_shift_output(date_from, date_to, shifts):
    average_shift_output = []

    if date_to - date_from < datetime.timedelta(days=14):
        with connections['jirkal_0003_fp'].cursor() as cursor:
            while date_from <= date_to:
                cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\')), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced), DateOfShift FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DateOfShift = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' GROUP BY DateOfShift')

                results = cursor.fetchone()

                if results:
                    average_shift_output.append(results[0])
                else:
                    average_shift_output.append(0)

                date_from += datetime.timedelta(days=1)
    else:
        with connections['jirkal_0003_fp'].cursor() as cursor:
            first_week = int(date_from.strftime("%V"))
            last_week = int(date_to.strftime("%V"))
            first_week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
            last_week_end = date_to + datetime.timedelta(days = 6 - date_from.weekday())

            cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\')), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced), DATEPART(ISO_WEEK, DateOfShift) FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DateOfShift >= \'{datetime.datetime.strftime(first_week_start, "%Y-%m-%d")}\' AND DateOfShift <= \'{datetime.datetime.strftime(last_week_end, "%Y-%m-%d")}\' GROUP BY DATEPART(ISO_WEEK, DateOfShift)')
                    
            results = cursor.fetchall()

            results_weeks = {week:result for (result, week) in results}

            weeks = range(first_week, last_week + 1)

            for week in weeks:
                if not week in results_weeks:
                    average_shift_output.append(0)
                else:
                    average_shift_output.append(results_weeks[week])

    return average_shift_output


def get_average_cycle_time(date_from, date_to, shifts):
    average_cycle_times = []

    if date_to - date_from < datetime.timedelta(days=14):
        with connections['jirkal_0003_fp'].cursor() as cursor:
            while date_from <= date_to:
                daily_produced_pieces = 0
                daily_aggregated_cycle_times = 0

                cursor.execute(f'WITH Shift_Statistics AS (SELECT Avg_CT, OK_Total, ShiftDate, CASE WHEN CONVERT(TIME, ShiftDate) >= \'06:00\' AND CONVERT(TIME, ShiftDate) < \'18:00\' THEN \'R\' ELSE \'O\' END AS Shift FROM TB_FP09_ShiftCounters_Statistic) SELECT Avg_CT, OK_Total, Shift, CONVERT(DATE, ShiftDate) AS "Shift Date" FROM Shift_Statistics WHERE Shift IN ({shifts_to_string(shifts)}) AND CONVERT(DATE, ShiftDate) = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND OK_Total > 0')
                results = cursor.fetchall()
                if results:
                    for shift_result in results:
                        daily_produced_pieces += shift_result[1]
                        daily_aggregated_cycle_times += shift_result[1] * shift_result[0]
                else:
                    pass

                try:
                    average_cycle_times.append(daily_aggregated_cycle_times / daily_produced_pieces)
                except:
                    average_cycle_times.append(None)

                date_from += datetime.timedelta(days=1)
    else:
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))

        with connections['jirkal_0003_fp'].cursor() as cursor:
            while first_week <= last_week:
                weekly_produced_pieces = 0
                weekly_aggregated_cycle_times = 0

                week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
                week_end = week_start + datetime.timedelta(days = 7)

                while week_start <= week_end:
                    cursor.execute(f'WITH Shift_Statistics AS (SELECT Avg_CT, OK_Total, ShiftDate, CASE WHEN CONVERT(TIME, ShiftDate) >= \'06:00\' AND CONVERT(TIME, ShiftDate) < \'18:00\' THEN \'R\' ELSE \'O\' END AS Shift FROM TB_FP09_ShiftCounters_Statistic) SELECT Avg_CT, OK_Total, Shift, CONVERT(DATE, ShiftDate) AS "Shift Date" FROM Shift_Statistics WHERE Shift IN ({shifts_to_string(shifts)}) AND CONVERT(DATE, ShiftDate) = \'{datetime.datetime.strftime(week_start, "%Y-%m-%d")}\' AND OK_Total > 0')
                    results = cursor.fetchall()
                    for shift_result in results:
                        weekly_produced_pieces += shift_result[1]
                        weekly_aggregated_cycle_times += shift_result[1] * shift_result[0]

                    week_start += datetime.timedelta(days = 1)

                try:
                    average_cycle_times.append(weekly_aggregated_cycle_times / weekly_produced_pieces)
                except:
                    average_cycle_times.append(None)

                first_week += 1
                date_from += datetime.timedelta(days = 7)

    return average_cycle_times


def shifts_to_string(shifts):
    shifts_string = [f"'{shift}'" for shift in shifts]
    return ", ".join(shifts_string)


def dates_to_x_axis(date_from, date_to):

    x_axis = []

    ### if the dates range is less than two weeks, we will be showing x axis as days
    if date_to - date_from < datetime.timedelta(days=14):
        while date_from <= date_to:
            x_axis.append(date_from.strftime("%Y-%m-%d"))
            date_from += datetime.timedelta(days=1)

    ### however, if the dates range is more than 14 days, we will be showing x axis as weeks
    if date_to - date_from >= datetime.timedelta(days=14):
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))

        if last_week >= first_week:
            while first_week <= last_week:
                x_axis.append((date_from - datetime.timedelta(days = date_from.weekday())).strftime("%Y-%m-%d"))
                date_from += datetime.timedelta(days = 7)
                first_week += 1
        else:
            last_week = last_week + 52
            while first_week <= last_week:
                x_axis.append((date_from - datetime.timedelta(days = date_from.weekday())).strftime("%Y-%m-%d"))
                date_from += datetime.timedelta(days = 7)
                first_week += 1

    return x_axis


def string_to_date(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%d")


def query_database(losses, loss_type, date_from, date_to, shifts):
    if loss_type == 'quality':  
        with connections['jirkal_0003_fp'].cursor() as cursor:
            while date_from <= date_to:
                cursor.execute(prepare_query(loss_type, date_from, shifts))
                results = cursor.fetchall()
                process_results(results, losses, loss_type, date_to > date_from + datetime.timedelta(days=14))
                date_from += datetime.timedelta(days=1)

    if loss_type in ('logistics', 'changeover', 'technical', 'organization', 'paint'):
        with connections['default'].cursor() as cursor:
            while date_from <= date_to:
                cursor.execute(prepare_query(loss_type, date_from, shifts))
                results = cursor.fetchall()
                process_results(results, losses, loss_type, date_to > date_from + datetime.timedelta(days=14))
                date_from += datetime.timedelta(days=1)

    if loss_type == 'performance':
                
        if date_to > date_from + datetime.timedelta(days=14):
            for loss_type in losses:
                if loss_type != 'performance':
                    temp_list = []
                    end_index = 7

                    while end_index <= len(losses[loss_type]) + 7:
                        temp_list.append(average(losses[loss_type][end_index-7:end_index]))
                        end_index += 7
                    losses[loss_type] = temp_list

        with connections['jirkal_0003_fp'].cursor() as cursor:
            index = 0
            if date_to - date_from < datetime.timedelta(days=14):
                while date_from <= date_to:
                    cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\')), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced), DateOfShift FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DateOfShift = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' GROUP BY DateOfShift')

                    results = cursor.fetchone()
                    
                    if results:
                        available_minutes = 480
                        production_time = (results[0] * 4.1) / 60
                        performance_loss = available_minutes - production_time
                        for loss in losses:
                            if loss != 'performance':
                                performance_loss -= losses[loss][index] if losses[loss][index] else 0
                        losses['performance'].append(performance_loss)
                    else:
                        losses['performance'].append(0)
                    date_from += datetime.timedelta(days=1)
                    index += 1
            else:
                first_week = int(date_from.strftime("%V"))
                last_week = int(date_to.strftime("%V"))
                first_week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
                last_week_end = date_to + datetime.timedelta(days = 6 - date_to.weekday())

                while first_week <= last_week:
                    cursor.execute(f'WITH ProductionData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus IN (\'25\', \'41\', \'89\', \'105\')), ShiftStatistics AS (SELECT COUNT(PartStatus) AS PartsProduced, DateOfShift, Shift FROM ProductionData GROUP BY DateOfShift, Shift) SELECT AVG(PartsProduced), DATEPART(ISO_WEEK, DateOfShift) FROM ShiftStatistics WHERE Shift IN ({shifts_to_string(shifts)}) AND DATEPART(ISO_WEEK, DateOfShift) >= \'{first_week}\' GROUP BY DATEPART(ISO_WEEK, DateOfShift)')

                    results = cursor.fetchone()

                    if results:
                        available_minutes = 480
                        production_time = (results[0] * 4.1) / 60
                        performance_loss = available_minutes - production_time
                        for loss in losses:
                            if loss != 'performance':
                                try:
                                    performance_loss -= losses[loss][index] 
                                except:
                                    pass
                        losses['performance'].append(performance_loss)
                    else:
                        losses['performance'].append(0)
                    first_week += 1
                    index += 1
        

def prepare_query(loss_type, date_from, shifts):
    if loss_type == 'quality':
        query = f'WITH NokData AS (SELECT PartStatus, CASE WHEN CONVERT(TIME, ProductionTime) >= \'06:00\' AND CONVERT(TIME, ProductionTime) < \'14:00\' THEN \'R\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'N\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' THEN CONVERT(DATE, (DATEADD(day, 1, ProductionTime))) ELSE CONVERT(DATE, ProductionTime) END AS DateOfShift FROM TB_FP09_QD WHERE PartStatus NOT IN (\'25\', \'41\', \'89\', \'105\') AND ProductionTime >= \'2022-11-01\'), NokShiftStatistics AS (SELECT COUNT(PartStatus) AS NokPartsProduced, DateOfShift, Shift FROM NokData GROUP BY DateOfShift, Shift) SELECT SUM(NokShiftStatistics.NokPartsProduced) FROM NokShiftStatistics WHERE NokShiftStatistics.Shift IN ({shifts_to_string(shifts)}) AND NokShiftStatistics.DateOfShift = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\''

    if loss_type == 'logistics':
        query = f'SET TIMEZONE = \'Europe/Prague\'; WITH logistics_losses_cte AS (SELECT category, downtime, station, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 18 THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 6 AND EXTRACT(HOUR FROM beginning_t) < 18 THEN \'R\' ELSE \'O\' END AS shift, end_t - beginning_t AS duration FROM fp09_downtimefromline WHERE category IN (\'Logistic / Logistika\', \'Input components + packaging / Vstupní komponenty + balení\')) SELECT SUM(duration) / COUNT(DISTINCT shift) FROM logistics_losses_cte WHERE shift IN ({shifts_to_string(shifts)}) AND shift_day = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND duration <= INTERVAL \'12 hours\' AND NOT downtime LIKE \'%lakov%\' GROUP BY shift_day'
    
    if loss_type == 'paint':
        query = f'SET TIMEZONE = \'Europe/Prague\'; WITH paint_losses_cte AS (SELECT category, downtime, station, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 18 THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 6 AND EXTRACT(HOUR FROM beginning_t) < 18 THEN \'R\' ELSE \'O\' END AS shift, end_t - beginning_t AS duration FROM fp09_downtimefromline WHERE category = \'Input components + packaging / Vstupní komponenty + balení\') SELECT SUM(duration) / COUNT(DISTINCT shift) FROM paint_losses_cte WHERE shift IN ({shifts_to_string(shifts)}) AND shift_day = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND duration <= INTERVAL \'12 hours\' AND downtime LIKE \'%lakov%\' GROUP BY shift_day'

    if loss_type == 'changeover':
        query = f'SET TIMEZONE = \'Europe/Prague\'; WITH changeover_losses_cte AS (SELECT category, downtime, station, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 22 THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 6 AND EXTRACT(HOUR FROM beginning_t) < 18 THEN \'R\' WHEN EXTRACT(HOUR FROM beginning_t) >= 14 AND EXTRACT(HOUR FROM beginning_t) < 22 THEN \'O\' ELSE \'N\' END AS shift, end_t - beginning_t AS duration FROM fp09_downtimefromline WHERE category = \'Changeover / Přestavba\') SELECT SUM(duration) / COUNT(DISTINCT shift) FROM changeover_losses_cte WHERE shift IN ({shifts_to_string(shifts)}) AND shift_day = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND duration <= INTERVAL \'12 hours\' GROUP BY shift_day'

    if loss_type == 'technical':
        query = f'SET TIMEZONE = \'Europe/Prague\'; WITH technical_losses_cte AS (SELECT category, downtime, station, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 22 THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 6 AND EXTRACT(HOUR FROM beginning_t) < 14 THEN \'R\' WHEN EXTRACT(HOUR FROM beginning_t) >= 14 AND EXTRACT(HOUR FROM beginning_t) < 22 THEN \'O\' ELSE \'N\' END AS shift, end_t - beginning_t AS duration FROM fp09_downtimefromline WHERE category IN (\'Repair, maintenance / Oprava, údržba\', \'Technical downtime / technický prostoj\')) SELECT SUM(duration) / COUNT(DISTINCT shift) FROM technical_losses_cte WHERE shift IN ({shifts_to_string(shifts)}) AND shift_day = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND duration <= INTERVAL \'12 hours\' GROUP BY shift_day'

    if loss_type == 'organization':
        query = f'SET TIMEZONE = \'Europe/Prague\'; WITH organization_losses_cte AS (SELECT category, downtime, station, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 22 THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= 6 AND EXTRACT(HOUR FROM beginning_t) < 14 THEN \'R\' WHEN EXTRACT(HOUR FROM beginning_t) >= 14 AND EXTRACT(HOUR FROM beginning_t) < 22 THEN \'O\' ELSE \'N\' END AS shift, end_t - beginning_t AS duration FROM fp09_downtimefromline WHERE category IN (\'Organization / Organizace\')) SELECT SUM(duration) / COUNT(DISTINCT shift) FROM organization_losses_cte WHERE shift IN ({shifts_to_string(shifts)}) AND shift_day = \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND duration <= INTERVAL \'12 hours\' GROUP BY shift_day'
    
    return query


def process_results(results, losses, loss_type, weeks_range):
    if loss_type == 'quality':
        if results[0][0] :
            losses['quality'].append(results[0][0] * 4.1 / 60)
        else:
            losses['quality'].append(0)

    if loss_type in ('logistics', 'changeover', 'technical', 'organization', 'paint'):
        if len(results) > 0:
            if results[0][0].total_seconds() / 60 <= 480:
                losses[loss_type].append(results[0][0].total_seconds() / 60)
            else:
                losses[loss_type].append(480)
        else:
            losses[loss_type].append(0)

    if loss_type == 'performance':
        if results:
            losses['performance']

@csrf_exempt
def service_book(request):

    if request.method == 'GET':

        stations = Station.objects.values_list('name', flat=True).exclude(name='NA').order_by('ordering')
        responsibles = User.objects.all().order_by('last_name').exclude(first_name='Recepce')
        categories = ["", "seřizovač", "údržba", "technologie", "IE", "KPS", "logistika", "RnD", "kvalita"]

        return render(request, 'fp09_service_book.html', {'stations': stations, 'responsibles': responsibles, 'categories': categories})

    if request.method == 'POST':

        request_body = json.loads(request.body)
    
        if request_body['action'] == 'getDowntimesSum':
            downtimes_sum = DowntimeFromLine.objects.filter(station=request_body['station'], category='Technical downtime / technický prostoj', beginning_t__gte=datetime.date.today() - datetime.timedelta(days=30)).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(hours=8)).aggregate(total_duration=Sum('duration'))['total_duration']

            return JsonResponse({'station': request_body['station'], 'downtimes': int(downtimes_sum.total_seconds() / 60) if downtimes_sum else 0})

        if request_body['action'] == 'getStatusDots':
            station = Station.objects.get(name=request_body['station'])
            cards_status = {
                'open_setter': ServiceBookAction.objects.filter(station=station, category='seřizovač', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_technology': ServiceBookAction.objects.filter(station=station, category='technologie', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_maintenance': ServiceBookAction.objects.filter(station=station, category='údržba', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_kps': ServiceBookAction.objects.filter(station=station, category='KPS', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_ie': ServiceBookAction.objects.filter(station=station, category='IE', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_rnd': ServiceBookAction.objects.filter(station=station, category='RnD', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_quality': ServiceBookAction.objects.filter(station=station, category='kvalita', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_logistics': ServiceBookAction.objects.filter(station=station, category='logistika', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'closed': ServiceBookAction.objects.filter(station=station, finish__isnull=False).count(),
                'backlog': ServiceBookAction.objects.filter(station=station, planned_finish__lt=datetime.date.today(), finish__isnull=True).count(),
            }
            return JsonResponse({'station': request_body['station'], 'status': cards_status})

        if request_body['action'] == 'deleteCard':
            ServiceBookAction.objects.filter(id=request_body['id']).delete()
            return JsonResponse({'status': 'okay'})

        if request_body['action'] == 'closeAction':
            ServiceBookAction.objects.filter(id=request_body['id']).update(finish=request_body['finish'])
            return JsonResponse({'status': 'okay'})

        if request_body['action'] == 'getStationActions':
            if request_body.get('filters', None):
                filters = request_body['filters']
            else:
                filters = {}
            if not request_body['station'] == 'all':
                station = Station.objects.get(name=request_body['station'])
                actions = ServiceBookAction.objects.filter(station=station).filter(**filters).annotate(sorting_priority=
                Case(
                    When(
                        Q(finish__isnull=True) & Q(planned_finish__lte=datetime.date.today()
                        ), then=0), 
                    When(
                        finish__isnull=False, then=2
                        ), 
                        default=1, output_field=IntegerField())).order_by('-sorting_priority', '-planned_finish')
            else:
                stations = Station.objects.all().order_by('name')
                actions = ServiceBookAction.objects.filter(station__in=stations).filter(**filters).annotate(sorting_priority=
                Case(
                    When(
                        Q(finish__isnull=True) & Q(planned_finish__lte=datetime.date.today()
                        ), then=0), 
                    When(
                        finish__isnull=False, then=2
                        ), 
                        default=1, output_field=IntegerField())).order_by('sorting_priority', 'planned_finish')

            data = {}
            for action in actions:
                data[action.title] = {}
                data[action.title]['id'] = action.id
                data[action.title]['description'] = action.description
                data[action.title]['responsible'] = action.responsible
                data[action.title]['category'] = action.category
                data[action.title]['priority'] = action.priority
                data[action.title]['status'] = action.status
                data[action.title]['planned_finish'] = str(action.planned_finish)
                data[action.title]['actions'] = list(action.servicebookactionentry_set.values_list('description', 'planned_end', 'id', 'owner'))
                data[action.title]['downtimes_addressed'] = list(action.addresseddowntime_set.values_list('downtime__name', flat=True))
                data[action.title]['closed'] = 'true' if action.finish else 'false'
                data[action.title]['finish'] = action.finish
                data[action.title]['backlog'] = 'true' if (not action.finish and action.planned_finish < datetime.date.today()) else 'false'
                data[action.title]['station'] = action.station.name
                
            return JsonResponse(data)

        if request_body['action'] == 'setStationAction':
            station = Station.objects.get(name=request_body['station'])
            service_action, created = ServiceBookAction.objects.update_or_create(title=request_body['data']['title'], station=station, defaults={
                'responsible': request_body['data']['responsible'],
                'category': request_body['data']['category'],
                'priority': request_body['data']['priority'],
                'status': request_body['data']['status'], 
                'planned_finish': request_body['data']['planned_finish'],
                'description': request_body['data']['description'],
            })

            service_action.servicebookactionentry_set.all().delete()
            service_action.addresseddowntime_set.all().delete()

            for action_comment in request_body['data']['actions']:
                action_comment_obj = ServiceBookActionEntry.objects.create(service_book_action = service_action, description=action_comment[1], planned_end=action_comment[0], owner=action_comment[2])

            for downtime_addressed in request_body['data']['downtimes_addressed']:
                downtime_addressed_obj = AddressedDowntime.objects.create(service_book_action = service_action, downtime = Downtime.objects.get(name = downtime_addressed))
                
            sendmail("Nová/aktualizovaná karta v akčním plánu FP09", service_action)

            return JsonResponse({'id': service_action.id})

        if request_body['action'] == 'getStationIssues':
            return JsonResponse({'downtimes': list(DowntimeFromLine.objects.filter(category='Technical downtime / technický prostoj', station=request_body.get('station', None), beginning_t__gte=datetime.date.today() - datetime.timedelta(days=60)).values('downtime').annotate(total_count=Count('id')).exclude(downtime__isnull=True).values('downtime', 'total_count').order_by('-total_count').values_list('downtime', 'total_count'))})


@csrf_exempt
def station_downtimes_detail(request):
    shift_models = {
        2: {
            'morning': (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
            'afternoon': (18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5),
            'next_day_start': 18,
        },
        3: {
            'morning': (6, 7, 8, 9, 10, 11, 12, 13),
            'afternoon': (14, 15, 16, 17, 18, 19, 20, 21),
            'next_day_start': 22,
        }
    }

    shifts_per_day = 3

    if request.method == 'GET':
        stations = Station.objects.all().order_by('ordering').values_list('name', flat=True)

    if request.method == 'POST':
        request_data = json.loads(request.body)
        station = Station.objects.get(name=request_data['station'])
        shifts = request_data.get('shifts', ('R', 'O'))
        date_from = datetime.datetime.strptime(request_data.get('date_from')[0:10], '%Y-%m-%d')
        date_to = datetime.datetime.strptime(request_data.get('date_to')[0:10], '%Y-%m-%d') + datetime.timedelta(days = 1)
        downtimes = request_data.get('downtimes', None)
        user_filters = {}

        if downtimes:
            user_filters['downtime__in'] = downtimes

        if request_data.get('type', None) == 'station_downtimes':
            return JsonResponse({'downtimes': list(DowntimeFromLine.objects.filter(station=station.name, beginning_t__gte=date_from, beginning_t__lt=date_to).values_list('downtime', flat=True).distinct('downtime'))})

        elif request_data.get('type', None) == 'station_actions':
            return JsonResponse({'actions': list(ServiceBookAction.objects.filter(station=station).values_list('title', flat=True).distinct('title'))})

        else:

            #### CHART ####

            chart_data_query = f'SET TIMEZONE = \'Europe/Prague\'; WITH cte AS (SELECT downtime, end_t - beginning_t AS duration, CASE WHEN EXTRACT(HOUR FROM beginning_t) IN {shift_models[shifts_per_day]["morning"]} THEN \'R\' WHEN EXTRACT(HOUR FROM beginning_t) IN {shift_models[shifts_per_day]["afternoon"]} THEN \'O\' ELSE \'N\' END AS shift, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= {shift_models[shifts_per_day]["next_day_start"]} THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_date FROM fp09_downtimefromline WHERE beginning_t >= \'{date_from}\' AND beginning_t <= \'{date_to}\' AND station = \'{station.name}\' {stringified_list(request_data.get("downtimes", []))}) SELECT SUM(duration), shift_date FROM cte WHERE shift IN {shifts} GROUP BY shift_date ORDER BY shift_date'

            with connections['default'].cursor() as cursor:
                cursor.execute(chart_data_query)
                rows = cursor.fetchall()
                downtimes_dict = {}
                for row in rows:
                    downtimes_dict[row[1]] = row[0]
            
            chart_labels = [date_from  + datetime.timedelta(days = _) for _ in range(0, (date_to - date_from).days)]
            chart_data = [downtimes_dict.get(_, datetime.timedelta(seconds=0)).total_seconds() for _ in chart_labels]

            #### AGGREGATION ####

            aggregation_data_query = f'SET TIMEZONE = \'Europe/Prague\'; WITH cte AS (SELECT downtime, end_t - beginning_t AS duration, CASE WHEN EXTRACT(HOUR FROM beginning_t) IN {shift_models[shifts_per_day]["morning"]} THEN \'R\' WHEN EXTRACT(HOUR FROM beginning_t) IN {shift_models[shifts_per_day]["afternoon"]} THEN \'O\' ELSE \'N\' END AS shift, CASE WHEN EXTRACT(HOUR FROM beginning_t) >= {shift_models[shifts_per_day]["next_day_start"]} THEN beginning_t::DATE + INTERVAL \'1 day\' ELSE beginning_t::DATE END AS shift_date FROM fp09_downtimefromline WHERE beginning_t >= \'{date_from}\' AND beginning_t <= \'{date_to}\' AND category = \'Technical downtime / technický prostoj\' AND station = \'{station.name}\') SELECT downtime, SUM(duration) FROM cte WHERE shift IN {shifts} GROUP BY downtime ORDER BY SUM(duration) DESC'

            with connections['default'].cursor() as cursor:
                cursor.execute(aggregation_data_query)
                rows = cursor.fetchall()
            
            aggregation_data = rows

            #### TIMELINE ####

            downtimes = DowntimeFromLine.objects.filter(station=station.name, beginning_t__gte=date_from, beginning_t__lt=date_to).filter(**user_filters).annotate(duration=F("end_t") - F("beginning_t")).values_list('downtime', 'beginning_t', 'end_t', 'duration', 'comment').order_by('-beginning_t')
            downtimes_list = [(_[0], str(_[1])[:19], str(_[2])[:19], _[3].total_seconds(), _[4]) for _ in downtimes]


            #### ACTIONS ####

            station_actions_full = ServiceBookAction.objects.filter(station=station, title__in=request_data['actions']).order_by('planned_finish')
            actions = []

            for action in station_actions_full:
                action_dict = {}
                action_dict['title'] = action.title
                action_dict['description'] = action.description
                action_dict['status'] = action.status
                action_dict['finish'] = str(action.planned_finish)
                action_dict['entries'] = []

                action_entries = ServiceBookActionEntry.objects.filter(service_book_action=action).order_by('planned_end')

                for entry in action_entries:
                    action_dict['entries'].append((buffered_label(entry.description)[0:10], str(entry.planned_end)))

                actions.append(action_dict)
            
            return JsonResponse({'chart_data': {'labels': [datetime.datetime.strftime(label, '%Y-%m-%d') for label in chart_labels], 'data': [int(_ / 60) for _ in chart_data]}, 'aggregation_data': [{k: int(v.total_seconds() / 60) for k, v in aggregation_data}], 'timeline_data': downtimes_list, 'actions_data': actions})

    return render(request, 'fp09_station_downtimes_detail.html', {'stations': stations})


def buffered_label(str):
    string_as_list = str.split(" ")
    return [" ".join(string_as_list[x:x+5]) for x in range(0, len(string_as_list), 5)]


def stringified_list(downtimes):
    return_string = ""
    if downtimes != []:
        return_string += "AND downtime IN ("
        return_string += ", ".join(f"'{w}'" for w in downtimes)
        return_string += ")"

    return return_string


def convert_to_strings(list_of_integers):
    return [str(x) for x in list_of_integers]


def sendmail(subject, card, from_email='automat@knorr-bremse.com'):
    html_template = 'email_message_new_card.html'
    send_to_user = card.responsible
    send_to_normalized = unidecode(send_to_user)
    send_to_address = f'{send_to_normalized.replace(" ", ".").lower()}@knorr-bremse.com'

    html_message = render_to_string(html_template, { 'card': card })

    message = EmailMessage(subject, html_message, from_email, (send_to_address, ), ("peter.vajda@knorr-bremse.com",))
    message.content_subtype = 'html'
    message.send()
    
    
def barcode_reader(request):
    downtime_id = request.GET.get('data').lstrip('0').rstrip("%0D")
    
    latest_downtime = DowntimeFromLine.objects.latest('beginning_t')
    
    downtime = Downtime.objects.get(id=downtime_id)
    
    try:
        latest_downtime.downtime = downtime.name
        latest_downtime.station = downtime.station
        latest_downtime.category = downtime.category
        latest_downtime.save()
    except Exception as e:
        print(e)
    
    return HttpResponse('okay')