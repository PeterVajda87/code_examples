import datetime
import json

from django.contrib.auth.models import User
from django.db import connections
from django.db.models import Case, IntegerField, Q, Sum, When
from django.db.models.functions import ExtractWeek
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from snowflake_connector.views import snowflake_query

from fp09.views import dates_to_x_axis, shifts_to_string, string_to_date
from snowflake_connector.views import snowflake_query

from .models import (AddressedDowntime, AvailabilityHelper, Downtime,
                     ServiceBookAction, ServiceBookActionEntry, ThingworxStatus, ThingworxDowntime)


@csrf_exempt
def performance_report(request):
    if request.method == 'GET':
        return render(request, 'obc4/performance_report.html', {})

    if request.method == 'POST':
        charts_data = {
        }

        request_data = json.loads(request.body)
        date_from = string_to_date(request_data['date_from'])
        date_to = string_to_date(request_data['date_to'])
        shifts = request_data.get('shifts', False)
        availability = request_data.get('availability', False)
        available_minutes = request_data.get('availableMinutes', False)

        if not availability:
            x_axis = dates_to_x_axis(date_from, date_to)

            charts_data['cycleTime'] = get_chart_data('average_cycle_time', date_from, date_to, x_axis, shifts)
            charts_data['averageShiftOutput'] = get_chart_data('average_shift_output', date_from, date_to, x_axis, shifts)
            charts_data['OEE'] = get_chart_data('oee', date_from, date_to, x_axis, shifts)
            charts_data['RQ'] = get_chart_data('rq', date_from, date_to, x_axis, shifts)
            charts_data['OEEsplit'] = get_chart_data('oee_split', date_from, date_to, x_axis, shifts)
            charts_data['losses'] = get_chart_data('losses', date_from, date_to, x_axis, shifts)
            
            return JsonResponse({'xAxis': x_axis, 'chartsData': charts_data})

        if availability:
            if available_minutes:
                AvailabilityHelper.objects.filter(shift_date=request_data.get('shift_date'), shift=request_data.get('shift')).update(available_minutes=available_minutes)
                return JsonResponse({'status': 'okay'})
            else:
                return JsonResponse({f'{value[0]} {value[1]}': value[2] for value in list(AvailabilityHelper.objects.filter(shift_date__gte=date_from, shift_date__lte=date_to).order_by('shift_date', 'shift_order').values_list('shift_date', 'shift', 'available_minutes'))})


def get_chart_data(chart_name, date_from, date_to, x_axis, shifts):
    if chart_name == 'average_cycle_time':
        return {
            'targetCT' : [30 for _ in x_axis],
            'CT': get_values(chart_name, date_from, date_to, shifts),
            }

    if chart_name == 'average_shift_output':
        return {
            'targetPCS': [800 for _ in x_axis],
            'PCS': get_values(chart_name, date_from, date_to, shifts),
        }

    if chart_name == 'oee':
        oee_ramp_up = {
            datetime.date(2022, 11, 29): 0.68,
            datetime.date(2022, 12, 27): 0.77,
            datetime.date(2023, 1, 24): 0.81,
            datetime.date(2023, 2, 21): 0.85
        }

        return {
            'targetOEE': [get_ramp_up_target(_, oee_ramp_up) for _ in x_axis],
            'OEE': get_values(chart_name, date_from, date_to, shifts),
        }

    if chart_name == 'rq':
        rq_ramp_up = {
            datetime.date(2022, 11, 29): 0.92,
            datetime.date(2022, 12, 27): 0.96,
            datetime.date(2023, 1, 24): 0.97,
            datetime.date(2023, 2, 21): 0.99
        }

        return {
            'targetRQ': [get_ramp_up_target(_, rq_ramp_up) for _ in x_axis],
            'RQ': get_values(chart_name, date_from, date_to, shifts),
        }

    if chart_name == 'oee_split':
        availability_ramp_up = {
            datetime.date(2022, 11, 29): 0.85,
            datetime.date(2022, 12, 27): 0.88,
            datetime.date(2023, 1, 24): 0.89,
            datetime.date(2023, 2, 21): 0.91
        }

        output_ramp_up = {
            datetime.date(2022, 11, 29): 0.89,
            datetime.date(2022, 12, 27): 0.92,
            datetime.date(2023, 1, 24): 0.93,
            datetime.date(2023, 2, 21): 0.95
        }

        rq_ramp_up = {
            datetime.date(2022, 11, 29): 0.92,
            datetime.date(2022, 12, 27): 0.96,
            datetime.date(2023, 1, 24): 0.97,
            datetime.date(2023, 2, 21): 0.99
        }

        return {
            'targetAvailability': [get_ramp_up_target(_, availability_ramp_up) for _ in x_axis],
            'targetOutput': [get_ramp_up_target(_, output_ramp_up) for _ in x_axis],
            'targetRQ': [get_ramp_up_target(_, rq_ramp_up) for _ in x_axis],
            'data': get_values(chart_name, date_from, date_to, shifts)

        }
    

def get_ramp_up_target(x_date, ramp_up_values):
    date_dt = datetime.date(int(x_date.split("-")[0]), int(x_date.split("-")[1]), int(x_date.split("-")[2]))
    for dt in ramp_up_values:
        if date_dt < dt:
            return ramp_up_values[dt]


def get_values(chart_name, date_from, date_to, shifts):
    return_data = []

    weeks = True if date_to - date_from >= datetime.timedelta(days=14) else False

    with connections['jirkal_0003_obc4'].cursor() as cursor:
        query_string = prepare_query(chart_name, date_from, date_to, shifts, weeks)
        results = cursor.execute(query_string).fetchall()
        process_results(return_data, results, date_from, date_to, weeks, shifts, chart_name)
            
    return return_data


def prepare_query(chart, date_from, date_to, shifts, weeks):
    if weeks == False:
        if chart == 'average_cycle_time':
            query_string = f'WITH cte AS (SELECT ProductionTime, DATEDIFF(second, LAG(ProductionTime, 1) OVER (ORDER BY ProductionTime), ProductionTime) AS ProductionDuration, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate, Result FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\') SELECT AVG(CAST(ProductionDuration AS FLOAT)), ShiftDate FROM cte WHERE ProductionDuration <= 60 AND ProductionDuration > 15 AND ShiftDate >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND Shift IN ({shifts_to_string(shifts)}) GROUP BY ShiftDate ORDER BY ShiftDate'

        if chart == 'average_shift_output':
            query_string = f'WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\' AND Result = \'OK\') SELECT CAST(COUNT(Result) AS FLOAT) / COUNT(DISTINCT(Shift)), ShiftDate FROM cte WHERE ShiftDate >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND Shift IN ({shifts_to_string(shifts)}) GROUP BY ShiftDate ORDER BY ShiftDate'

        if chart == 'oee':
            query_string = f'WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\' AND Result = \'OK\') SELECT (COUNT(Result) * 0.5) / (480 * COUNT(DISTINCT Shift)), ShiftDate FROM cte WHERE ShiftDate >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND Shift IN ({shifts_to_string(shifts)}) GROUP BY ShiftDate ORDER BY ShiftDate'

        if chart == 'rq':
            query_string = f'WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\') SELECT COUNT(CASE WHEN Result = \'OK\' THEN 1 ELSE NULL END) / CAST(COUNT(Result) AS FLOAT), ShiftDate FROM cte WHERE ShiftDate >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND Shift IN ({shifts_to_string(shifts)}) GROUP BY ShiftDate ORDER BY ShiftDate'

        if chart == 'oee_split':
            query_string = f'WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\') SELECT CAST(COUNT(Result) AS FLOAT) / COUNT(DISTINCT(Shift)) * 0.5 / 450 AS average_output, CAST(450 AS FLOAT) / 480 AS average_availability, COUNT(CASE WHEN Result = \'OK\' THEN 1 ELSE NULL END) / CAST(COUNT(Result) AS FLOAT) AS average_quality, ShiftDate FROM cte WHERE ShiftDate >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND ShiftDate <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND Shift IN ({shifts_to_string(shifts)}) GROUP BY ShiftDate ORDER BY ShiftDate'


    if weeks == True:
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))
        last_week_of_year = datetime.datetime(year = date_from.year, month = 12, day = 28).isocalendar()[1]
        
        weeks = []
        
        if last_week > first_week:
            weeks.append(list(range(first_week, last_week + 1)))
        else:
            while first_week <= last_week_of_year:
                weeks.append(first_week)
                first_week += 1
            weeks.extend(list(range(1, last_week + 1)))

    
        if chart == 'average_cycle_time':
            query_string = f'WITH cte AS (SELECT ProductionTime, DATEDIFF(second, LAG(ProductionTime, 1) OVER (ORDER BY ProductionTime), ProductionTime) AS ProductionDuration, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate, Result FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\') SELECT AVG(CAST(ProductionDuration AS FLOAT)), DATEPART(ISO_WEEK, ShiftDate) FROM cte WHERE ProductionDuration <= 60 AND ProductionDuration > 15 AND DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate) ORDER BY DATEPART(ISO_WEEK, ShiftDate)'
            
        if chart == 'average_shift_output':
            query_string = f"""WITH cte AS 
            (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) >= \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\' AND Result = \'OK\'),
            cte2 AS (SELECT DISTINCT Shift, ShiftDate, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte),

            cte3 AS (SELECT week, COUNT(*) AS weekly_shift_count FROM cte2 WHERE shift IN ({shifts_to_string(shifts)}) GROUP BY week),

            cte4 AS (SELECT CAST(COUNT(Result) AS FLOAT) AS output, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte WHERE DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate))

            SELECT output / cte3.weekly_shift_count, cte4.week FROM cte4 LEFT JOIN cte3 on cte3.week = cte4.week
            """
            print(query_string)

        if chart == 'oee':
            query_string = f"""WITH cte AS 
            (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\' AND Result = \'OK\'),
            cte2 AS (SELECT DISTINCT Shift, ShiftDate, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte),

            cte3 AS (SELECT week, COUNT(*) AS weekly_shift_count FROM cte2 GROUP BY week),

            cte4 AS (SELECT CAST(COUNT(Result) AS FLOAT) AS output, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte WHERE DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate))

            SELECT (output * 0.5) / (480 * cte3.weekly_shift_count), cte4.week FROM cte4 LEFT JOIN cte3 on cte3.week = cte4.week
            """

        if chart == 'rq':
            query_string = f'WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\') SELECT COUNT(CASE WHEN Result = \'OK\' THEN 1 ELSE NULL END) / CAST(COUNT(Result) AS FLOAT), DATEPART(ISO_WEEK, ShiftDate) FROM cte WHERE DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate) ORDER BY DATEPART(ISO_WEEK, ShiftDate)'

        if chart == 'oee_split':
            query_string = f"""
            WITH cte AS (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\'),
            
            cte2 AS (SELECT CAST(COUNT(Result) AS FLOAT) / COUNT(DISTINCT(Shift)) * 0.5 / 450 AS average_output, CAST(450 AS FLOAT) / 480 AS average_availability, COUNT(CASE WHEN Result = \'OK\' THEN 1 ELSE NULL END) / CAST(COUNT(Result) AS FLOAT) AS average_quality, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte WHERE DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate)),

            cte3 AS 
            (SELECT Result, CASE WHEN CONVERT(TIME, ProductionTime) >= \'22:00\' OR CONVERT(TIME, ProductionTime) < \'06:00\' THEN \'N\' WHEN CONVERT(TIME, ProductionTime) > \'14:00\' AND CONVERT(TIME, ProductionTime) < \'22:00\' THEN \'O\' ELSE \'R\' END AS Shift, CASE WHEN CONVERT(TIME, ProductionTime) > \'22:00\' THEN CONVERT(DATE, DATEADD(day, 1, ProductionTime)) ELSE CONVERT(DATE, ProductionTime) END AS ShiftDate FROM TB_OBC_04_QD WHERE ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=1), "%Y-%m-%d")}\' AND Result = \'OK\'),

            cte4 AS (SELECT DISTINCT Shift, ShiftDate, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte3),

            cte5 AS (SELECT week, COUNT(*) AS weekly_shift_count FROM cte4 GROUP BY week),

            cte6 AS (SELECT CAST(COUNT(Result) AS FLOAT) AS output, DATEPART(ISO_WEEK, ShiftDate) AS week FROM cte3 WHERE DATEPART(ISO_WEEK, ShiftDate) IN ({str(weeks).lstrip("[").rstrip("]")}) AND Shift IN ({shifts_to_string(shifts)}) GROUP BY DATEPART(ISO_WEEK, ShiftDate)),

            cte7 AS (SELECT (cte6.output / (900 * cte5.weekly_shift_count)) as average_output, cte6.week FROM cte6 LEFT JOIN cte5 on cte5.week = cte6.week)

            SELECT cte7.average_output, cte2.average_availability, cte2.average_quality, cte2.week FROM cte7
            LEFT JOIN cte2 ON cte2.week = cte7.week
            ORDER BY cte7.week
            """

    return query_string


def process_results(return_list, results, date_from, date_to, weeks, shifts, chart_name):
    results_temp = {value[-1]: ([*value[0:-1]] if len(value) > 1 else value[0]) for value in results}

    if chart_name == 'oee_split':
        for date_key in results_temp:
            if type(date_key) == datetime.date:
                theoretical_availability = 480 * len(shifts)
                real_availability = AvailabilityHelper.objects.filter(shift_date=date_key, shift__in=shifts).aggregate(availability=Sum('available_minutes'))['availability']
                results_temp[date_key][1] = real_availability / theoretical_availability
            else: # here we are working with weeks
                theoretical_availability = 480 * len(shifts) * 7 # because we suppose 5 days a week
                real_availability = AvailabilityHelper.objects.filter(shift__in=shifts).annotate(week=ExtractWeek('shift_date')).values('week', 'available_minutes').filter(week=date_key).aggregate(availability=Sum('available_minutes'))['availability']
                results_temp[date_key][1] = real_availability / theoretical_availability
                
    if chart_name == 'oee':
        for date_key in results_temp:
            if type(date_key) == datetime.date:
                theoretical_availability = 480 * len(shifts)
                real_availability = AvailabilityHelper.objects.filter(shift_date=date_key, shift__in=shifts).aggregate(availability=Sum('available_minutes'))['availability']
                results_temp[date_key][0] = float(results_temp[date_key][0]) / (real_availability / theoretical_availability)
            else: # here we are working with weeks
                theoretical_availability = 480 * len(shifts) * 5 # because we suppose 5 days a week
                real_availability = AvailabilityHelper.objects.filter(shift__in=shifts, shift_date__gte=date_from - datetime.timedelta(weeks=1), shift_date__lte = date_to + datetime.timedelta(weeks=1)).exclude(shift_date__iso_week_day__gte=6).annotate(week=ExtractWeek('shift_date')).values('week', 'available_minutes').filter(week=date_key).aggregate(availability=Sum('available_minutes'))['availability']
                results_temp[date_key][0] = results_temp[date_key][0] / (real_availability / theoretical_availability)


    if weeks:
        first_week = int(date_from.strftime("%V"))
        last_week = int(date_to.strftime("%V"))
        last_week_of_year = datetime.datetime(year = date_from.year, month = 12, day = 28).isocalendar()[1]
        
        x_axis_range = []
        
        if last_week > first_week:
            x_axis_range.extend(list(range(first_week, last_week + 1)))
        else:
            while first_week <= last_week_of_year:
                x_axis_range.append(first_week)
                first_week += 1
            x_axis_range.extend(list(range(1, last_week + 1)))
    else:
        x_axis_range = list(reversed([(date_to - datetime.timedelta(days=_)).date() for _ in range((date_to - date_from).days + 1)]))

    for tick in x_axis_range:
        return_list.append(results_temp.get(tick, None))

    return return_list

 
@csrf_exempt
def service_book(request):

    if request.method == 'GET':
        stations_query = "SELECT DISTINCT IDStation FROM [OBC_04].[dbo].[AlarmsAll]"

        with connections['jirkal_117'].cursor() as cursor:
            cursor.execute(stations_query)
            data = cursor.fetchall()

        stations = [tup[0] for tup in data]

        responsibles = User.objects.all().order_by('last_name').exclude(first_name='Recepce')
        categories = ["", "seřizovač", "údržba", "technologie", "IE", "KPS", "logistika", "RnD"]

        return render(request, 'obc4/obc4_service_book.html', {'stations': stations, 'responsibles': responsibles, 'categories': categories})

    if request.method == 'POST':

        request_body = json.loads(request.body)
    
        if request_body['action'] == 'getDowntimesSum':
            downtimes_sum_query = f"""
            SELECT SUM(DATEDIFF(second, TimeStampAlarmStart, TimeStampAlarmEnd)) / 60 FROM [OBC_04].[dbo].[AlarmsAll] WHERE TimeStampAlarmStart > '{datetime.date.today() - datetime.timedelta(days=30)}' AND IDStation = {request_body["station"]} AND DATEDIFF(second, TimeStampAlarmStart, TimeStampAlarmEnd) < 28800 AND AlarmType = 1 AND LineMode = 1 GROUP BY IDStation
            """

            with connections['jirkal_117'].cursor() as cursor:
                cursor.execute(downtimes_sum_query)

                data = cursor.fetchall()

            return JsonResponse({'station': request_body['station'], 'downtimes': data[0]})

        if request_body['action'] == 'getStatusDots':
            station = request_body['station']
            cards_status = {
                'open_setter': ServiceBookAction.objects.filter(station=station, category='seřizovač', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_technology': ServiceBookAction.objects.filter(station=station, category='technologie', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_maintenance': ServiceBookAction.objects.filter(station=station, category='údržba', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_kps': ServiceBookAction.objects.filter(station=station, category='KPS', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_ie': ServiceBookAction.objects.filter(station=station, category='IE', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
                'open_rnd': ServiceBookAction.objects.filter(station=station, category='RnD', finish__isnull=True, planned_finish__gte=datetime.date.today()).count(),
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
                station = request_body['station']
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
                stations_query = "SELECT DISTINCT IDStation FROM [OBC_04].[dbo].[AlarmsAll]"

                with connections['jirkal_117'].cursor() as cursor:
                    cursor.execute(stations_query)
                    data = cursor.fetchall()

                stations = [tup[0] for tup in data]
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
                data[action.title]['station'] = action.station
                
            return JsonResponse(data)

        if request_body['action'] == 'setStationAction':
            station = request_body['station']
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

            return JsonResponse({'id': service_action.id})

        if request_body['action'] == 'getStationIssues':
            station_issues_query = f"""SELECT AlarmTextCZ, COUNT(IDStation)
            FROM AlarmsAll
            WHERE TimeStampAlarmStart >= '{datetime.date.today() - datetime.timedelta(days=60)}'
            AND AlarmType = 1 AND LineMode = 1
            GROUP BY AlarmTextCZ
            ORDER BY COUNT(IDStation) DESC
            """

            with connections['jirkal_117'].cursor() as cursor:
                cursor.execute(station_issues_query)

                data = cursor.fetchall()

            return JsonResponse({'downtimes': data})


def get_downtimes(request, date_from, date_to):
    query = f"SELECT SUBSTATUS, STATUSTIME FROM SMARTKPI_MACHINESTATUSDATA WHERE MACHINE = 'KBLIBOBC04-90-ActuationAndFinishingStationThing' AND STATUS <> 'KBMaschStatus.1.OI.AutoSet' AND STATUSTIME >= '{date_from}' AND STATUSTIME <= '{date_to}' ORDER BY STATUSTIME"
    
    results = snowflake_query(query)
    
    thingworx_statuses = ThingworxStatus.objects.values_list('status_text_2', 'category')
    
    downtime_categories = {status_text_2: category for status_text_2, category in thingworx_statuses}
    
    categorized_downtimes = [(result[0], result[1], results[index+1][1] if index + 1 < len(results) else 0, downtime_categories.get(result[0], "Technical")) for index, result in enumerate(results)]   
    
    for categorized_downtime in categorized_downtimes:
        try:
            ThingworxDowntime.objects.update_or_create(downtime_beginning=categorized_downtime[1], downtime_end=categorized_downtime[2], defaults={'downtime_text_thingworx': categorized_downtime[0], 'downtime_category': categorized_downtime[3]})
        except:
            pass

def prepare_dates_graph(weeks, start_time, end_time):
    if weeks == False:
        dates = [start_time.date()+datetime.timedelta(days=x) for x in range((end_time - start_time).days)]
        line_x = [date.strftime("%Y-%m-%d") for date in dates]
    else:
        first_week = int(start_time.strftime("%V"))
        last_week = int(end_time.strftime("%V"))
        # line_x = {}
        # current_week = first_week
        # current_date = start_time
        # week_end = end_time + datetime.timedelta(days=6 - end_time.weekday())
        
        # while current_week <= last_week:
        #     line_x[current_week] = current_date.strftime("%Y-%m-%d")
        #     current_date += datetime.timedelta(weeks=1)
        #     current_week = int(current_date.strftime("%V"))

        first_week = int(start_time.strftime("%V"))
        last_week = int(end_time.strftime("%V"))
        line_x = []
        current_week = first_week
        current_date = start_time
        week_end = end_time + datetime.timedelta(days=6 - end_time.weekday())

        while current_week <= last_week:
            line_x.append(current_date.strftime("%Y-%m-%d"))
            current_date += datetime.timedelta(weeks=1)
            current_week = int(current_date.strftime("%V"))

        last_value = datetime.datetime.strptime(line_x[-1], "%Y-%m-%d")
        if (last_value <= week_end):
            line_x.pop()
        # Pokud týden neskončil -> vyhodí datum ze slovníku line_x
        # last_value = datetime.datetime.strptime(list(line_x.values())[-1], "%Y-%m-%d")
        # if (last_value < week_end):
        #     line_x.popitem()
    return line_x
           
@csrf_exempt
def losses(request):
    if request.method == "GET":
        context = {}
        
        return render(request, 'obc4/losses.html', context)
    
    if request.method == "POST":
        request_data = json.loads(request.body)
        # chart_type = request_data['chart_id']
        #######
        date_from = datetime.datetime.strptime(request_data.get('date_from'),'%Y-%m-%d')
        date_to = datetime.datetime.strptime(request_data.get('date_to'),'%Y-%m-%d')
        shifts = request_data.get("shifts")
        # Ranni smena; Prumer trvani je jenom soucet, kdyz zvoli vic smen, musim secit trvani prostoju a vydelit poctem smen v ten den
        get_downtimes(request, date_from, date_to)
        weeks = True if date_to - date_from >= datetime.timedelta(days=14) else False

        x_axis_labels = prepare_dates_graph(weeks, date_from, date_to)

        def shifts_to_string(shifts):
            shifts_string = [f"'{shift}'" for shift in shifts] 
            return ", ".join(shifts_string)
        
        with connections['default'].cursor() as cursor:
            #psql
            if weeks == False:
                query = f'WITH shifts_cte AS (SELECT downtime_category, CASE WHEN EXTRACT(HOUR FROM downtime_beginning) >= 18 THEN downtime_beginning::DATE + INTERVAL \'1 day\' ELSE downtime_beginning::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM downtime_beginning) >= 6 AND EXTRACT(HOUR FROM downtime_beginning) < 18 THEN \'R\' ELSE \'O\' END AS shift, downtime_end - downtime_beginning AS duration FROM obc4_thingworxdowntime) SELECT shift_day::DATE, downtime_category, EXTRACT(MINUTE FROM SUM(duration) / COUNT(DISTINCT shift)) FROM shifts_cte WHERE downtime_category <> \'Production\' AND shift_day >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND shift_day <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND shift IN ({shifts_to_string(shifts)}) GROUP BY downtime_category, shift_day ORDER BY shift_day'
            else:
                first_week = int(date_from.strftime("%V"))
                last_week = int(date_to.strftime("%V"))
                query = f'WITH shifts_week_cte AS (SELECT downtime_category, CASE WHEN EXTRACT(HOUR FROM downtime_beginning) >= 18 THEN downtime_beginning::DATE + INTERVAL \'1 day\' ELSE downtime_beginning::DATE END AS shift_day, CASE WHEN EXTRACT(HOUR FROM downtime_beginning) >= 6 AND EXTRACT(HOUR FROM downtime_beginning) < 18 THEN \'R\' ELSE \'O\' END AS shift, downtime_end - downtime_beginning AS duration FROM obc4_thingworxdowntime WHERE downtime_beginning >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\') SELECT EXTRACT(WEEK FROM shift_day), downtime_category, EXTRACT(MINUTE FROM SUM(duration) / COUNT(DISTINCT shift)) FROM shifts_week_cte WHERE downtime_category <> \'Production\' AND EXTRACT(WEEK FROM shift_day) >= {first_week} AND EXTRACT(WEEK FROM shift_day) <= {last_week} AND shift IN ({shifts_to_string(shifts)}) GROUP BY downtime_category, EXTRACT(WEEK FROM shift_day) ORDER BY EXTRACT(WEEK FROM shift_day)'
            
            cursor.execute(query)
            results = cursor.fetchall()
            #print(f"Vysledek query: {results}")
            
        with connections['jirkal_117'].cursor() as cursor:
            #tsql
            if weeks == False:
                query_idstation = f'WITH shifts_cte AS (SELECT IDStation, CASE WHEN DATEPART(HOUR, CAST(TimeStampAlarmStart AS datetime)) >= 18 THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS date)) ELSE CAST(TimeStampAlarmStart AS date) END AS shift_day, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= 6 AND DATEPART(HOUR, TimeStampAlarmStart) < 18 THEN \'R\' ELSE \'O\' END AS shift, DATEDIFF(minute, CAST(TimeStampAlarmStart AS datetime), CAST(TimeStampAlarmEnd AS datetime)) AS duration FROM [OBC_04].[dbo].[AlarmsAll] WHERE LineMode = 1) SELECT shift_day, IDStation, SUM(duration) / COUNT(DISTINCT shift) / 60 FROM shifts_cte WHERE shift_day >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND shift_day <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND shift IN ({shifts_to_string(shifts)}) GROUP BY IDStation, shift_day ORDER BY shift_day'
            else:
                query_idstation = f'WITH shifts_cte AS (SELECT IDStation, CASE WHEN DATEPART(HOUR, CAST(TimeStampAlarmStart AS datetime)) >= 18 THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS date)) ELSE CAST(TimeStampAlarmStart AS date) END AS shift_day, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= 6 AND DATEPART(HOUR, TimeStampAlarmStart) < 18 THEN \'R\' ELSE \'O\' END AS shift, DATEDIFF(minute, CAST(TimeStampAlarmStart AS datetime), CAST(TimeStampAlarmEnd AS datetime)) AS duration FROM [OBC_04].[dbo].[AlarmsAll] WHERE LineMode = 1 AND TimeStampAlarmStart >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\') SELECT DATEPART(week, shift_day), IDStation, SUM(duration) / COUNT(DISTINCT shift) / 60 FROM shifts_cte WHERE DATEPART(week,shift_day) >= {first_week} AND DATEPART(week, shift_day) <= {last_week} AND shift IN ({shifts_to_string(shifts)}) GROUP BY IDStation, DATEPART(week, shift_day) ORDER BY DATEPART(week,shift_day)'
            cursor.execute(query_idstation)
            idstations = cursor.fetchall()
            #print(f"Vysledek query: {idstations}")
        
        with connections['jirkal_117'].cursor() as cursor:
            #tsql
            if weeks == False:
                query_alarmtext = f'WITH shifts_cte AS (SELECT AlarmTextCz, CASE WHEN DATEPART(HOUR, CAST(TimeStampAlarmStart AS datetime)) >= 18 THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS date)) ELSE CAST(TimeStampAlarmStart AS date) END AS shift_day, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= 6 AND DATEPART(HOUR, TimeStampAlarmStart) < 18 THEN \'R\' ELSE \'O\' END AS shift, DATEDIFF(minute, CAST(TimeStampAlarmStart AS datetime), CAST(TimeStampAlarmEnd AS datetime)) AS duration FROM [OBC_04].[dbo].[AlarmsAll] WHERE LineMode = 1) SELECT shift_day, AlarmTextCz, SUM(duration) / COUNT(DISTINCT shift) / 60 FROM shifts_cte WHERE shift_day >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND shift_day <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND shift IN ({shifts_to_string(shifts)}) GROUP BY AlarmTextCz, shift_day ORDER BY shift_day'
            else:
                query_alarmtext = f'WITH shifts_cte AS (SELECT AlarmTextCz, CASE WHEN DATEPART(HOUR, CAST(TimeStampAlarmStart AS datetime)) >= 18 THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS date)) ELSE CAST(TimeStampAlarmStart AS date) END AS shift_day, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= 6 AND DATEPART(HOUR, TimeStampAlarmStart) < 18 THEN \'R\' ELSE \'O\' END AS shift, DATEDIFF(minute, CAST(TimeStampAlarmStart AS datetime), CAST(TimeStampAlarmEnd AS datetime)) AS duration FROM [OBC_04].[dbo].[AlarmsAll] WHERE LineMode = 1 AND TimeStampAlarmStart >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\') SELECT DATEPART(week, shift_day), AlarmTextCz, SUM(duration) / COUNT(DISTINCT shift) / 60 FROM shifts_cte WHERE DATEPART(week,shift_day) >= {first_week} AND DATEPART(week, shift_day) <= {last_week} AND shift IN ({shifts_to_string(shifts)}) GROUP BY AlarmTextCz, DATEPART(week, shift_day) ORDER BY DATEPART(week,shift_day)'

            cursor.execute(query_alarmtext)
            alarmtexts = cursor.fetchall()
            #print(f"Vysledek query: {alarmtexts}")

        # with connections['jirkal_117'].cursor() as cursor:
        #    query musi mit TimeStampAlarmEnd, TimeStampAlarmStart, IDStation WHERE LineMode = 1
        #    ta nam rekne soucet prostoju po stanici 
        #   tahle Y os bude mit data group by IDStation
        
        #   query musi mit TimeStampAlarmEnd, TimeStampAlarmStart, AlarmTextCz WHERE LineMode = 1
        #   tahle Y os bude mit data GROUP BY AlarmTextCz
        
        
        def group_by_category(data, weeks, weeks_range):
            result = {}
            try:
                start_date = min(item[0] for item in data)
                end_date = max(item[0] for item in data)
                # get the number of days or weeks
                num_of_days = (end_date - start_date).days if not weeks else weeks_range
            except:
                pass
            for item in data:
                date, category, value = item
                if category not in result:
                    result[category] = [0] * num_of_days 
                # get the index to store the value
                try:    
                    index = date.day - start_date.day if not weeks else int(date.isocalendar()[1]) - int(start_date.isocalendar()[1])
                except:
                     index = date.day - start_date.day if not weeks else int(date) - int(start_date)
                if index < num_of_days:
                    try:
                        result[category][index] = int(value)
                    except: 
                        pass
                        #result[category][index] = value
            return result
        
        ##########
        # data ready
        first_week = int(date_from.strftime(" %V"))
        last_week = int(date_to.strftime("%V"))
        len_weeks = len(list(range(first_week, last_week)))

        #print(results)
        # return JsonResponse({'chart_data': get_loss_data(chart_type, date_from, date_to)})
        # potrebujeme z dat, ktere zavolame niz nakreslit ten hezky graf jak na FP09
        # zatim klidne pracuj s dummy datami na frontendu
        # tzn {'technical_losses': [80, 50, 20], 'dummy_blabla': [40, 40, 40]}
        # 'technical_losses'
        # 'organizational_losses'
        # 'logistics',
        # 'maintenance',
        # 'production'
        # aby dummy data byly snadno nahraditelne volanim na server (fetch (a dotahnu si je z DB))
        # format dummy dat necham na Simonovi, ale musi tam byt X(den/tyden), Y(hodnota v minutach)
        y_axis_values = group_by_category(results, weeks, len_weeks)
        y_axis_idstations = group_by_category(idstations, weeks, len_weeks)
        y_axis_alarmtexts = group_by_category(alarmtexts, weeks, len_weeks)
        y_axis_alarmtexts = group_by_category(alarmtexts, weeks, len_weeks)
        y_axis_idstations = group_by_category(idstations, weeks, len_weeks)
        
        #y_axis_values = {'technical_losses' : [80, 50, 20, 90], 'organizational_losses': [87, 65, 25, 87], 'logistics': [54, 64, 21, 52], 'maintenance': [46, 89, 65, 120], 'production': [44, 98, 35, 78]}
        
        #y_axis_technical_problem = {'technical_problem_1': [52, 56, 56, 89], 'technical_problem_2': [54,54,61,84], 'technical_problem_3': [32,14,35,78], 'technical_problem_4': [12,54,64,37], 'technical_problem_5': [45,32,35,97]}
        
        # BONUS TASK
        # kdyz je rozsah datumu vic nez 14 dnu, tak x_osa obsahuje TYDNY
        # [1, 2, 3, 4] - prvni az ctvrty tyden v lednu
        
        # {'2023-01-19': {
        # 'technical_losses': 70,
        # 'organization_losses': 90
        # },
        
        # '2023-01-20: {
        #     '
        context = {
            'x_axis_labels': x_axis_labels,
            'y_axis_values': y_axis_values,
            'y_axis_alarmtexts': y_axis_alarmtexts,
            'y_axis_idstations': y_axis_idstations,
        }
    return JsonResponse(context)

@csrf_exempt
def prestavby(request):
    if request.method == "GET":

        date_from = datetime.datetime.strptime('2023-01-02', '%Y-%m-%d')
        date_to = datetime.datetime.strptime('2023-01-15', '%Y-%m-%d')
        print(date_from, date_to)
        #shifts = request_data.get("shifts")
        check_buttons = ('R','O','N')

        #//////////////////////////////////////////////////////////////////////////
        weeks = True if date_to - date_from >= datetime.timedelta(days=14) else False
        x_axis_labels = prepare_dates_graph(weeks, date_from, date_to)
        print(x_axis_labels)
        with connections['jirkal_117'].cursor() as cursor:
            if weeks == False:
                query_prestavby = f'WITH shifts_cte AS (SELECT KBType, ProductionTime, LAG(KBType, 1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumber, LAG(ProductionTime,1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumberProductionTime, CASE WHEN DATEPART(HOUR,ProductionTime) > 22 THEN DATEADD(day,1,ProductionTime) ELSE ProductionTime END AS shift_day, CASE WHEN DATEPART(HOUR,ProductionTime) >= 6 AND DATEPART(HOUR,ProductionTime) < 14 THEN \'R\' WHEN DATEPART(HOUR,ProductionTime) >= 14 AND DATEPART(HOUR,ProductionTime) < 22 THEN \'O\' ELSE \'N\' END AS shift FROM [OBC_04].[dbo].[TB_OBC_04_QD] WHERE KBType IS NOT NULL), changeover_cte AS ( SELECT KBType, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(SECOND, PreviousOrderNumberProductionTime, ProductionTime)) OVER (partition by KBType) as medianval FROM shifts_cte WHERE PreviousOrderNumber <> KBType), filtered_changeovers AS (SELECT * FROM shifts_cte WHERE KBType <> PreviousOrderNumber AND shift_day >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND shift_day <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime) < (SELECT 2 * AVG(medianval) FROM changeover_cte) ) SELECT CAST(shift_day AS date), CAST(AVG(DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime)) as integer) FROM filtered_changeovers WHERE KBType <> PreviousOrderNumber AND shift IN {check_buttons} GROUP BY CAST(shift_day as date) ORDER BY CAST(shift_day AS date)'
            else:
                first_week = int(date_from.strftime("%V"))
                last_week = int(date_to.strftime("%V"))
                query_prestavby = f'WITH shifts_cte AS (SELECT KBType, ProductionTime, LAG(KBType, 1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumber, LAG(ProductionTime,1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumberProductionTime, CASE WHEN DATEPART(HOUR,ProductionTime) > 22 THEN DATEADD(day,1,ProductionTime) ELSE ProductionTime END AS shift_day, CASE WHEN DATEPART(HOUR,ProductionTime) >= 6 AND DATEPART(HOUR,ProductionTime) < 14 THEN \'R\' WHEN DATEPART(HOUR,ProductionTime) >= 14 AND DATEPART(HOUR,ProductionTime) < 22 THEN \'O\' ELSE \'N\' END AS shift FROM [OBC_04].[dbo].[TB_OBC_04_QD] WHERE KBType IS NOT NULL), changeover_cte AS ( SELECT KBType, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(SECOND, PreviousOrderNumberProductionTime, ProductionTime)) OVER (partition by KBType) as medianval FROM shifts_cte WHERE PreviousOrderNumber <> KBType), filtered_changeovers AS (SELECT * FROM shifts_cte WHERE KBType <> PreviousOrderNumber AND ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\' AND DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime) < (SELECT 2 * AVG(medianval) FROM changeover_cte)) SELECT DATEPART(week,CAST(shift_day AS date)), CAST(AVG(DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime)) as integer) FROM filtered_changeovers WHERE KBType <> PreviousOrderNumber AND shift IN {check_buttons} AND DATEPART(week,CAST(shift_day as date)) >= {first_week} AND DATEPART(week, CAST(shift_day as date)) <= {last_week} GROUP BY DATEPART(week, CAST(shift_day as date)) ORDER BY DATEPART(week, CAST(shift_day as date))'
            print(query_prestavby)
            cursor.execute(query_prestavby)
            prestavby = cursor.fetchall()
            print(f"Vysledek query: {prestavby}")

            def group_by_category(data, weeks, len_weeks, dates_array):
                if weeks:
                    result = {i: 0 for i in range(1, len_weeks + 1)}
                    for week, avg in data:
                        result[week] = avg
                    return result
                else:
                    result = {}
                    start = (datetime.datetime.strptime(dates_array[0], '%Y-%m-%d').date()).toordinal()
                    end = (datetime.datetime.strptime(dates_array[-1], '%Y-%m-%d').date()).toordinal()
                    for i in range(start, end + 1):
                        date = datetime.date.fromordinal(i)
                        result[date] = 0
                    for date, avg in data:
                        result[date] = avg
                    return result
                
            first_week = int(date_from.strftime(" %V"))
            last_week = int(date_to.strftime("%V"))
            len_weeks = len(list(range(first_week, last_week)))

            line_y = group_by_category(prestavby, weeks, len_weeks, x_axis_labels)
            print(line_y)
            #//////////////////////////////////////////////
        context = {}
        
        return render(request, 'obc4/prestavby.html', context)

    if request.method == "POST":
        #request_data = json.loads(request.body)
        #date_from = datetime.datetime.strptime(request_data.get('date_from'),'%Y-%m-%d')
        #date_to = datetime.datetime.strptime(request_data.get('date_to'),'%Y-%m-%d')
        #shifts = request_data.get("shifts")
        
        def shifts_to_string(shifts):
            shifts_string = [f"'{shift}'" for shift in shifts] 
            return ", ".join(shifts_string)
        
        weeks = True if date_to - date_from >= datetime.timedelta(days=14) else False
        x_axis_labels = prepare_dates_graph(weeks, date_from, date_to)
        with connections['jirkal_117'].cursor() as cursor:
            if weeks == False:
                query_prestavby = f'WITH shifts_cte AS (SELECT OrderNumber, ProductionTime, LAG(OrderNumber, 1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumber, LAG(ProductionTime,1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumberProductionTime, CASE WHEN DATEPART(HOUR,ProductionTime) > 22 THEN DATEADD(day,1,ProductionTime) ELSE ProductionTime END AS shift_day, CASE WHEN DATEPART(HOUR,ProductionTime) >= 6 AND DATEPART(HOUR,ProductionTime) < 14 THEN \'R\' WHEN DATEPART(HOUR,ProductionTime) >= 14 AND DATEPART(HOUR,ProductionTime) < 22 THEN \'O\' ELSE \'N\' END AS shift FROM [OBC_04].[dbo].[TB_OBC_04_QD] WHERE OrderNumber IS NOT NULL), changeover_cte AS ( SELECT OrderNumber, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(SECOND, PreviousOrderNumberProductionTime, ProductionTime)) OVER (partition by OrderNumber) as medianval FROM shifts_cte WHERE PreviousOrderNumber <> OrderNumber), filtered_changeovers AS (SELECT * FROM shifts_cte WHERE OrderNumber <> PreviousOrderNumber AND shift_day >= \'{datetime.datetime.strftime(date_from, "%Y-%m-%d")}\' AND shift_day <= \'{datetime.datetime.strftime(date_to, "%Y-%m-%d")}\' AND DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime) < (SELECT 2 * AVG(medianval) FROM changeover_cte) ) SELECT CAST(shift_day AS date), CAST(AVG(DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime)) as integer) FROM filtered_changeovers WHERE OrderNumber <> PreviousOrderNumber AND shift IN ({shift_to_string(check_buttons)}) GROUP BY CAST(shift_day as date) ORDER BY CAST(shift_day AS date)'
            else:
                first_week = int(date_from.strftime("%V"))
                last_week = int(date_to.strftime("%V"))
                query_prestavby = f'WITH shifts_cte AS (SELECT OrderNumber, ProductionTime, LAG(OrderNumber, 1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumber, LAG(ProductionTime,1) OVER (ORDER BY ProductionTime) AS PreviousOrderNumberProductionTime, CASE WHEN DATEPART(HOUR,ProductionTime) > 22 THEN DATEADD(day,1,ProductionTime) ELSE ProductionTime END AS shift_day, CASE WHEN DATEPART(HOUR,ProductionTime) >= 6 AND DATEPART(HOUR,ProductionTime) < 14 THEN \'R\' WHEN DATEPART(HOUR,ProductionTime) >= 14 AND DATEPART(HOUR,ProductionTime) < 22 THEN \'O\' ELSE \'N\' END AS shift FROM [OBC_04].[dbo].[TB_OBC_04_QD] WHERE OrderNumber IS NOT NULL), changeover_cte AS ( SELECT OrderNumber, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(SECOND, PreviousOrderNumberProductionTime, ProductionTime)) OVER (partition by OrderNumber) as medianval FROM shifts_cte WHERE PreviousOrderNumber <> OrderNumber), filtered_changeovers AS (SELECT * FROM shifts_cte WHERE OrderNumber <> PreviousOrderNumber AND ProductionTime >= \'{datetime.datetime.strftime(date_from - datetime.timedelta(days=7), "%Y-%m-%d")}\' AND DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime) < (SELECT 2 * AVG(medianval) FROM changeover_cte)) SELECT DATEPART(week,CAST(shift_day AS date)), CAST(AVG(DATEDIFF(second, PreviousOrderNumberProductionTime, ProductionTime)) as integer) FROM filtered_changeovers WHERE OrderNumber <> PreviousOrderNumber AND shift IN ({shifts_to_string(check_buttons)}) AND DATEPART(week,CAST(shift_day as date)) >= {first_week} AND DATEPART(week, CAST(shift_day as date)) <= {last_week} GROUP BY DATEPART(week, CAST(shift_day as date)) ORDER BY DATEPART(week, CAST(shift_day as date))'
            # print(query_prestavby)
            cursor.execute(query_prestavby)
            prestavby = cursor.fetchall()
            # print(f"Vysledek query: {prestavby}")

            def group_by_category(data, weeks, len_weeks, dates_array):
                if weeks:
                    result = {i: 0 for i in range(1, len_weeks + 1)}
                    for week, avg in data:
                        result[week] = avg
                    return result
                else:
                    result = {}
                    start = (datetime.datetime.strptime(dates_array[0], '%Y-%m-%d').date()).toordinal()
                    end = (datetime.datetime.strptime(dates_array[-1], '%Y-%m-%d').date()).toordinal()
                    for i in range(start, end + 1):
                        date = datetime.date.fromordinal(i)
                        result[date] = 0
                    for date, avg in data:
                        result[date] = avg
                    return result
                
            first_week = int(date_from.strftime(" %V"))
            last_week = int(date_to.strftime("%V"))
            len_weeks = len(list(range(first_week, last_week)))

            line_y = group_by_category(prestavby, weeks, len_weeks, x_axis_labels)


        context = {
            'x_axis_labels': x_axis_labels,
            'y_axis_values': line_y,
        }
        return JsonResponse(context)

def get_loss_data(loss_type, date_from, date_to):
    if loss_type == 'technical_losses':
        connection = connections['jirkal_0003_obc04']
        cursor = connection.cursor()
        
        cursor.execute(
        f"""
        SELECT SUM()
        """
        )
        
        connection.close()


@csrf_exempt
def check_if_falsified(request):
    request_data = json.loads(request.body)
    shifts = request_data['shifts']
    period = request_data['date']
    stripped_period = period[5:]
    stripped_period = stripped_period.lstrip("(").rstrip(")")
    period_items = stripped_period.split(", ")
    period_year = period_items[0]
    period_month = int(period_items[1]) + 1
    period_day = period_items[2]
        
    shift_date = datetime.date(int(period_year), period_month, int(period_day))
    
    result = True if AvailabilityHelper.objects.filter(shift_date=shift_date, shift__in=shifts).exclude(available_minutes=480).exists() else False
    
    return JsonResponse({'falsified': result})