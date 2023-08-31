from django.http.response import HttpResponse, JsonResponse
from django.views.decorators import csrf
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import datetime
import random
from .models import LanicoMontaz
from django.db.models.functions import ExtractHour
from django.db.models import F, Sum, Count, When, Case, Q, Value, CharField, IntegerField, ExpressionWrapper, DurationField 
from statistics import mean, median
import numpy as np
from fp09.views import string_to_date, dates_to_x_axis, shifts_to_string
from django.db import connections
from django.db.models.functions import ExtractWeek
from django.contrib.auth.models import User
from django.db.models import Sum, When, Case, Q, IntegerField, Avg
from snowflake_connector.views import snowflake_query


@csrf_exempt
def performance_report(request):
    if request.method == "GET":

        return render(request, 'fp_lanico_performance_report.html', {})

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
            'targetCT' : [7.5 for _ in x_axis],
            'CT': get_average_cycle_time(date_from, date_to, shifts),
            }

    if chart_name == 'oee':
        return {
            'targetOEE': [70 for _ in x_axis],
            'OEE': get_oee(date_from, date_to, shifts),
        }

def get_average_cycle_time(date_from, date_to, shifts):
    if date_to - date_from < datetime.timedelta(days=14):

        averagetimes = snowflake_query(f"SELECT CASE WHEN (hour(EndDate) >= 21 OR hour(EndDate) < 5) THEN 'N' WHEN (hour(EndDate) >= 5 AND hour(EndDate) < 13) THEN 'R' ELSE 'O' END AS Shift, CASE WHEN (hour(EndDate) >= 21) THEN TIMEADD(day, 1, EndDate)::DATE ELSE EndDate::DATE END AS ShiftDate, AVG(Difference), COUNT(*) FROM (SELECT Machine,PRODUCTIONTIME,lag(PRODUCTIONTIME, 1) OVER (PARTITION BY Machine = 'KBLIBFP-LanicoMachineThing' ORDER BY PRODUCTIONTIME ASC) AS EndDate, DATEDIFF(second, EndDate, PRODUCTIONTIME) AS Difference FROM PROD.M_DIGI_MANUFACTURING.SMARTKPI WHERE Machine = 'KBLIBFP-LanicoMachineThing' AND PRODUCTIONTIME > '{date_from}' AND PRODUCTIONTIME < '{date_to}') WHERE Difference > 0 AND Difference < 20 GROUP BY Shift, ShiftDate ORDER BY ShiftDate")
        delta = datetime.timedelta(days=1)
        list_of_dates = {}
        list_of_dates_sum = {}
        average_cycle_times = []

        while date_from <= date_to:
            list_of_dates[date_from] = []
            list_of_dates_sum[date_from] = []
            date_from += delta
        
        for shift, date, average, sum_of_pieces in averagetimes:
            if shift in shifts:
                list_of_dates[datetime.datetime.combine(date, datetime.datetime.min.time())].append(average)
                list_of_dates_sum[datetime.datetime.combine(date, datetime.datetime.min.time())].append(sum_of_pieces)

        for (k, v), (k2, v2) in zip(list_of_dates.items(), list_of_dates_sum.items()):
            sum_of_parts = sum(v2)
            if sum_of_parts != 0:
                times = ([v[i] * v2[i] for i in range(len(v))])
                average_cycle_times.append(sum(times) / sum_of_parts)
            else:
                average_cycle_times.append(0)
    else:
        average_cycle_times = []
        week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
        week_end = week_start + datetime.timedelta(days = 7)
        while week_start <= date_to:
            time_all_temporary = 0
            sum_of_pieces_temporary = 0
            averagetimes = snowflake_query(f"SELECT CASE WHEN (hour(EndDate) >= 21 OR hour(EndDate) < 5) THEN 'N' WHEN (hour(EndDate) >= 5 AND hour(EndDate) < 13) THEN 'R' ELSE 'O' END AS Shift, CASE WHEN (hour(EndDate) >= 21) THEN TIMEADD(day, 1, EndDate)::DATE ELSE EndDate::DATE END AS ShiftDate, AVG(Difference), COUNT(*) FROM (SELECT Machine,PRODUCTIONTIME,lag(PRODUCTIONTIME, 1) OVER (PARTITION BY Machine = 'KBLIBFP-LanicoMachineThing' ORDER BY PRODUCTIONTIME ASC) AS EndDate, DATEDIFF(second, EndDate, PRODUCTIONTIME) AS Difference FROM PROD.M_DIGI_MANUFACTURING.SMARTKPI WHERE Machine = 'KBLIBFP-LanicoMachineThing' AND PRODUCTIONTIME > '{week_start}' AND PRODUCTIONTIME < '{week_end}') WHERE Difference > 0 AND Difference < 20 GROUP BY Shift, ShiftDate ORDER BY ShiftDate")
            for shift, date, average, sum_of_pieces in averagetimes:
                if shift in shifts:
                    time_all_temporary += average * sum_of_pieces
                    sum_of_pieces_temporary += sum_of_pieces
            if sum_of_pieces_temporary != 0:
                average_cycle_times.append(time_all_temporary / sum_of_pieces_temporary)
            else:
                average_cycle_times.append(0)
            week_start += datetime.timedelta(days = 7)
            week_end += datetime.timedelta(days = 7)
    
    return average_cycle_times

def get_oee(date_from, date_to, shifts):
    if date_to - date_from < datetime.timedelta(days=14):
        average_oee = []
        averagetimes = snowflake_query(f"SELECT CASE WHEN (hour(EndDate) >= 21 OR hour(EndDate) < 5) THEN 'N' WHEN (hour(EndDate) >= 5 AND hour(EndDate) < 13) THEN 'R' ELSE 'O' END AS Shift, CASE WHEN (hour(EndDate) >= 21) THEN TIMEADD(day, 1, EndDate)::DATE ELSE EndDate::DATE END AS ShiftDate, AVG(Difference), COUNT(*) FROM (SELECT Machine,PRODUCTIONTIME,lag(PRODUCTIONTIME, 1) OVER (PARTITION BY Machine = 'KBLIBFP-LanicoMachineThing' ORDER BY PRODUCTIONTIME ASC) AS EndDate, DATEDIFF(second, EndDate, PRODUCTIONTIME) AS Difference FROM PROD.M_DIGI_MANUFACTURING.SMARTKPI WHERE Machine = 'KBLIBFP-LanicoMachineThing' AND PRODUCTIONTIME > '{date_from}' AND PRODUCTIONTIME < '{date_to}') GROUP BY Shift, ShiftDate ORDER BY ShiftDate")
 
        delta = datetime.timedelta(days=1)
        list_of_dates = {}
        list_of_dates_sum = {}
        average_cycle_times = []

        while date_from <= date_to:
            list_of_dates[date_from] = []
            list_of_dates_sum[date_from] = []
            date_from += delta
        
        for shift, date, average, sum_of_pieces in averagetimes:
            if shift in shifts:
                if date is not None:
                        if sum_of_pieces > 500:
                            list_of_dates[datetime.datetime.combine(date, datetime.datetime.min.time())].append(average)
                            list_of_dates_sum[datetime.datetime.combine(date, datetime.datetime.min.time())].append(sum_of_pieces)

        for (k, v), (k2, v2) in zip(list_of_dates.items(), list_of_dates_sum.items()):
            sum_of_parts = sum(v2)
            sum_of_shifts = len(v2)
            if sum_of_parts != 0:
                average_oee.append((sum_of_parts * 7.5) * 100 / (sum_of_shifts * 8 * 60 * 60) )
            else:
                average_oee.append(None)
    else:
        average_oee = []
        week_start = date_from - datetime.timedelta(days = date_from.weekday()) 
        week_end = week_start + datetime.timedelta(days = 7)
        while week_start <= date_to:
            shifts_temporary = 0
            sum_of_pieces_temporary = 0
            averagetimes = snowflake_query(f"SELECT CASE WHEN (hour(EndDate) >= 21 OR hour(EndDate) < 5) THEN 'N' WHEN (hour(EndDate) >= 5 AND hour(EndDate) < 13) THEN 'R' ELSE 'O' END AS Shift, CASE WHEN (hour(EndDate) >= 21) THEN TIMEADD(day, 1, EndDate)::DATE ELSE EndDate::DATE END AS ShiftDate, AVG(Difference), COUNT(*) FROM (SELECT Machine,PRODUCTIONTIME,lag(PRODUCTIONTIME, 1) OVER (PARTITION BY Machine = 'KBLIBFP-LanicoMachineThing' ORDER BY PRODUCTIONTIME ASC) AS EndDate, DATEDIFF(second, EndDate, PRODUCTIONTIME) AS Difference FROM PROD.M_DIGI_MANUFACTURING.SMARTKPI WHERE Machine = 'KBLIBFP-LanicoMachineThing' AND PRODUCTIONTIME > '{week_start}' AND PRODUCTIONTIME < '{week_end}') GROUP BY Shift, ShiftDate ORDER BY ShiftDate")
            for shift, date, average, sum_of_pieces in averagetimes:
                if shift in shifts:
                    if sum_of_pieces > 500:
                        shifts_temporary += 1
                        sum_of_pieces_temporary += sum_of_pieces
            if shifts_temporary != 0:
                average_oee.append((sum_of_pieces_temporary * 7.5) * 100 / (shifts_temporary * 8 * 60 * 60))
            else:
                average_oee.append(0)
            week_start += datetime.timedelta(days = 7)
            week_end += datetime.timedelta(days = 7)

    return average_oee




@csrf_exempt
def fp_lanico_performance(request):

    if request.method == "POST":
        request_data = json.loads(request.body)
        first_interval_start = datetime.datetime.strptime(request_data['first_interval_start'], "%Y-%m-%d")
        first_interval_end = datetime.datetime.strptime(request_data['first_interval_end'], "%Y-%m-%d")
        second_interval_start = datetime.datetime.strptime(request_data['second_interval_start'], "%Y-%m-%d")
        second_interval_end = datetime.datetime.strptime(request_data['second_interval_end'], "%Y-%m-%d")
        button = request_data['button_option']
        used_colors = {}

        if button == "Cycle Time [s] Hourly":
            days_first = 24
            days_in_range_first = ["0:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00", "7:00-8:00", "8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00", "15:00-16:00", "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00", "20:00-21:00", "21:00-22:00", "22:00-23:00", "23:00-00:00"]
            datasets1, average1, median1, ninty1, dictionary_partnumber1 = get_mean_cycle_time_hourly(first_interval_start, first_interval_end, used_colors)
            days_second = 24
            days_in_range_second = ["0:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00", "7:00-8:00", "8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00", "15:00-16:00", "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00", "20:00-21:00", "21:00-22:00", "22:00-23:00", "23:00-00:00"]
            datasets2, average2, median2, ninty2, dictionary_partnumber2 = get_mean_cycle_time_hourly(second_interval_start, second_interval_end, used_colors)
        if button == "Cycle Time [s] Daily":
            days_first, days_in_range_first, datasets1, average1, median1, ninty1, dictionary_partnumber1 = get_mean_cycle_time_daily(first_interval_start, first_interval_end, used_colors)
            days_second, days_in_range_second, datasets2, average2, median2, ninty2, dictionary_partnumber2 = get_mean_cycle_time_daily(second_interval_start, second_interval_end, used_colors)

        return_data = {
            'days_first': days_first,
            'days_in_range_first': days_in_range_first,
            'datasets1': datasets1,
            'days_second': days_second,
            'days_in_range_second': days_in_range_second,
            'datasets2': datasets2,
            'average1': average1,
            'median1': median1,
            'ninty1': ninty1,
            'average2': average2,
            'median2': median2,
            'ninty2': ninty2,
            'dictionary_partnumber1': dictionary_partnumber1,
            'dictionary_partnumber2': dictionary_partnumber2
        }

        return JsonResponse(return_data)

    if request.method == "GET":

        return render(request, 'fp_lanico_performance.html')


def setColor(category, used_colors):

    if category in used_colors:
        color = used_colors[category]
    else:
        r = random.randint(0,255)
        g = random.randint(0,255)
        b = random.randint(0,255)
        color = f'rgb({r}, {g}, {b})'
        used_colors[category] = color

    return color, used_colors

def get_mean_cycle_time_hourly(interval_start, interval_end, used_colors):

    TypesFP = list(LanicoMontaz.objects.filter(Cas__gte = interval_start, Cas__lte = interval_end).values_list('Typ_fp', flat=True).distinct())

    datasets1 = []
    list_of_cycle_times = []
    dictionary_partnumber = {}
    #dictionary_partnumber['TypeFP'] = (average, median0, ninty)


    list_of_times_included = [[] for i in range(24)]
    print("START")
    print(datetime.datetime.now())
    for TypeFP in TypesFP:
        if TypeFP != "":
            list_of_times_included = [[] for i in range(24)]
            with connections['jirkal_0003'].cursor() as cursor:
                cursor.execute(f'SELECT Cas, Interval FROM Lanico_montaz WHERE Typ_FP = \'{TypeFP}\'AND Cas > \'{interval_start}\' AND Cas < \'{interval_end}\' AND Interval < 20')       
                cycle_times = cursor.fetchall()
            #cycle_times = list(LanicoMontaz.objects.filter(Cas__gte = interval_start, Cas__lte = interval_end, Typ_fp = TypeFP, Interval__lte = 20).order_by('Cas').values_list('Cas', 'Interval'))
                for time, interval in cycle_times:
                    list_of_times_included[time.hour].append(interval)
                    list_of_cycle_times.append(interval)
                dictionary_partnumber[TypeFP] = (round(mean(list_of_cycle_times), 2), round(median(list_of_cycle_times), 2), round(np.percentile(list_of_cycle_times, 90), 2))
                list_of_averages = [sum(sub_list) / (len(sub_list) or 1) for sub_list in list_of_times_included]
                dataset = {}
                dataset['label'] = TypeFP
                dataset['data'] = list_of_averages
                dataset['tooltips'] = []
                color, used_colors = setColor(TypeFP, used_colors)
                dataset['borderColor'] = color
                for data in list_of_averages:
                    dataset['tooltips'].append(f"Mean value| {round(data, 2)}")
                datasets1.append(dataset)

    average = round(mean(list_of_cycle_times), 2)
    median0 = round(median(list_of_cycle_times,), 2)
    ninty = round(np.percentile(list_of_cycle_times, 90),2)

    return datasets1, average, median0, ninty, dictionary_partnumber


def get_mean_cycle_time_daily(interval_start, interval_end, used_colors):

    days_in_range = []
    days = 0
    datetime_iteration = interval_start
    list_of_cycle_times = []
    every_record = []

    while datetime_iteration.date() <= interval_end.date():
        days_in_range.append(datetime_iteration.date())
        datetime_iteration = datetime_iteration + datetime.timedelta(days=1)
        days += 1
    
    TypesFP = list(LanicoMontaz.objects.filter(Cas__gte = interval_start, Cas__lte = interval_end, Interval__lte = 20).values_list('Typ_fp', flat=True).distinct())

    datasets1 = []
    dictionary_partnumber = {}

    for TypeFP in TypesFP:
        if TypeFP != "":
            list_of_averages = [[] for i in range(days)]
            i = 0
            for day_in_range in days_in_range:
                cycle_times = list(LanicoMontaz.objects.filter(Cas__gte = day_in_range, Cas__lte = day_in_range + datetime.timedelta(days=1), Interval__lte = 20, Typ_fp = TypeFP).values_list('Interval', flat=True))
                for interval in cycle_times:
                    every_record.append(interval)
                    list_of_cycle_times.append(interval)
                list_of_averages[i] = sum(cycle_times) / (len(cycle_times) or 1)
                i += 1

            dictionary_partnumber[TypeFP] = (round(mean(list_of_cycle_times), 2), round(median(list_of_cycle_times), 2), round(np.percentile(list_of_cycle_times, 90), 2))

            dataset = {}
            dataset['label'] = TypeFP
            dataset['data'] = list_of_averages
            dataset['tooltips'] = []
            color, used_colors = setColor(TypeFP, used_colors)
            dataset['borderColor'] = color
            for data in list_of_averages:
                dataset['tooltips'].append(f"Mean value| {data}")
            datasets1.append(dataset)

    average = round(mean(every_record), 2)
    median0 = round(median(every_record,), 2)
    ninty = round(np.percentile(every_record, 90),2)

    return days, days_in_range, datasets1, average, median0, ninty, dictionary_partnumber