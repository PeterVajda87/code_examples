from unicodedata import category
from django.http import JsonResponse
from django.shortcuts import render
from numpy import char, outer
from thingworx.models import Tb_fp09_alarms, Tb_fp09_alarmstext
from .models import ChartType, Station, Dashboard, Chart
from fp09.models import DowntimeFromLine
from django.db.models import F, Count, Sum
from django.db import connections
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
import re
import datetime
from django.db.models.functions import TruncDate, ExtractHour
from django.db.models import When, Case, Value, CharField, DateTimeField, ExpressionWrapper, DurationField


def index(request):

    context = {
        'stations': list(Station.objects.values_list('name', flat=True)),
        'alarms': get_alarms(None, stations=Station.objects.all),
    }

    return render(request, 'fp09/ps_index.html', context)


def dashboard(request):

    dashboard = Dashboard.objects.filter().first()
    chart_types = ChartType.objects.all()

    if dashboard:
        charts = dashboard.chart_set.all()
    else:
        charts = ""

    context = {
        'dashboard': dashboard,
        'charts': charts,
        'chart_types': chart_types,
    }

    return render(request, 'fp09/ps_dashboard.html', context)


@csrf_exempt
def get_chart_data(request):

    chart = Chart.objects.get(id = json.loads(request.body)['chartId'])

    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(chart.query)
            results = cursor.fetchall()

    except:
        results = ""

    data = {
        'results': results,
    }

    return JsonResponse({'data': data})


@csrf_exempt
def edit_chart_meta_data(request):

    request_data = json.loads(request.body)

    dashboard = Dashboard.objects.get(id = request_data['dashboardId'])
    
    chart_id = request_data['chartId']

    if chart_id == "0":
        chart = Chart.objects.create()
    else:
        chart = Chart.objects.get(id = request_data['chartId'])
 
    chart.dashboard.add(dashboard)
    chart.author = request.user
    chart.name = request_data['name']
    chart.type = ChartType.objects.get(type = request_data['type'])
    chart.query = request_data['query']
    chart.save()

    return JsonResponse({'chartId': chart.id})


def update_stations():
    for station_short, station_long in [(re.search('Alarms(.*)\[', code).group(1), code) for code in Tb_fp09_alarms.objects.values_list('alarmcode', flat=True).distinct()]:
        Station.objects.update_or_create(name=station_short, defaults = {'codename' : station_long})


def get_alarms(request = None, stations = [], duration=True, frequency=True, beginning=datetime.date.today() - datetime.timedelta(days=1), end=datetime.date.today()):

    alarms = list(Tb_fp09_alarms.objects.filter(timestampalarm__gte=beginning, timestampalarmend__lte=end).values('alarmcode').annotate(alarm_duration=Sum('alarmtime'), alarm_count=Count('alarmtime')).order_by('-alarm_duration'))

    alarm_texts = list(Tb_fp09_alarmstext.objects.filter(alarmcode__in=Tb_fp09_alarms.objects.filter(timestampalarm__gte=beginning, timestampalarmend__lte=end).values_list('alarmcode', flat=True)).values_list('alarmcode', 'alarmtext'))

    alarm_dict = {k: v for (k, v) in alarm_texts}

    for alarm in alarms:
        alarm['alarmcode'] = alarm_dict.get(alarm['alarmcode'], 'Undefined')
        alarm['alarm_duration'] = int(alarm['alarm_duration']/1000)

    return alarms


def svg_charts(request):

    date_to = datetime.datetime.now()
    date_from = date_to - datetime.timedelta(days=10)

    data = DowntimeFromLine.objects.exclude(category__isnull=True).exclude(station__isnull=True).exclude(downtime__isnull=True).exclude(end_t__isnull=True).filter(beginning_t__gte=date_from, beginning_t__lt=date_to).exclude(end_t__gte=F('beginning_t') + datetime.timedelta(hours=8))
    
    categories = [tup[0] for tup in list(data.values('category').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('category', 'duration'))]

    chart_data_categories = {
        'type': 'column',
        'data': {
            'labels': categories,
            'title': 'Prostoje po kategoriích (v minutách)',
            'datasets': [
                {
                    'label': 'categories',
                    'tableColumn': 'category',
                    'values': [round(data.filter(category=category).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for category in categories],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    dates = data.annotate(calendar_date=TruncDate('beginning_t')).values_list('calendar_date', flat=True).distinct('calendar_date').order_by('calendar_date')

    string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

    chart_data_trend_categories = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostojů v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'categories trend',
                    'tableColumn': 'category',
                    'values': [round(data.filter(category=categories[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=categories[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    stations = [tup[0] for tup in list(data.filter(category=categories[0]).values('station').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('station', 'duration'))[:9]]

    chart_data_stations = {
        'type': 'column',
        'data': {
            'labels': stations,
            'title': f'Prostoje po stanicích v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations',
                    'tableColumn': 'station',
                    'values': [round(data.filter(station=station, category=categories[0]).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for station in stations],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    chart_data_trend_stations = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostojů na stanici {stations[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations trend',
                    'tableColumn': 'category',
                    'values': [round(data.filter(category=categories[0], station=stations[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=categories[0], station=stations[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    downtimes = [tup[0] for tup in list(data.filter(category=categories[0], station=stations[0]).values('downtime').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('downtime', 'duration'))[:9]]

    chart_data_downtimes = {
        'type': 'column',
        'data': {
            'labels': downtimes,
            'title': f'Prostoje stanice {stations[0]} v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations',
                    'tableColumn': 'downtime',
                    'values': [round(data.filter(station=stations[0], category=categories[0], downtime=downtime).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for downtime in downtimes],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    chart_data_trend_downtimes = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostoje na stanici {stations[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'downtimes trend',
                    'tableColumn': 'downtime',
                    'values': [round(data.filter(category=categories[0], station=stations[0], downtime=downtimes[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=categories[0], station=stations[0], downtime=downtimes[0], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }
 
    return render(request, 'fp09/ps_svg_charts.html', {'data_categories': chart_data_categories, 'data_stations': chart_data_stations, 'data_downtimes': chart_data_downtimes, 'data_trend_categories': chart_data_trend_categories, 'data_trend_stations': chart_data_trend_stations, 'data_trend_downtimes': chart_data_trend_downtimes})


@csrf_exempt
def svg_charts_fetch(request):
    parameters = json.loads(request.body)

    date_to = datetime.datetime.strptime(parameters["date_to"], "%a, %d %b %Y %H:%M:%S %Z")
    date_from = datetime.datetime.strptime(parameters["date_from"], "%a, %d %b %Y %H:%M:%S %Z")
    shifts = parameters.get('shifts', ['R', 'O', 'N'])

    shifts_count = 3

    shift_model = {
        2: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 'afternoon_shift_hours': [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]},
        3: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13], 'afternoon_shift_hours': [14, 15, 16, 17, 18, 19, 20, 21]}
    }

    data = DowntimeFromLine.objects.exclude(category__isnull=True).exclude(station__isnull=True).exclude(end_t__isnull=True).annotate(hour_start=ExtractHour('beginning_t')).annotate(shift=Case(When(hour_start__in=shift_model[shifts_count]['morning_shift_hours'], then=Value('R')), When(hour_start__in=shift_model[shifts_count]['afternoon_shift_hours'], then=Value('O')), default=Value('N'), output_field=CharField())).filter(shift__in=shifts).annotate(shift_day=Case(When(hour_start__gte=18, then=F('beginning_t') + datetime.timedelta(days = 1)), output_field=DateTimeField()), default=F('beginning_t')).filter(beginning_t__gte=date_from, beginning_t__lt=date_to + datetime.timedelta(days=1)).exclude(end_t__gte=F('beginning_t') + datetime.timedelta(hours=8))

    chart_to_update = parameters['chart_to_update']

    if chart_to_update == 'categories':
        try:
            categories = [tup[0] for tup in list(data.values('category').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('category', 'duration'))]

            chart_data = {
                'type': 'column',
                'data': {
                    'labels': categories,
                    'title': 'Prostoje po kategoriích (v minutách)',
                    'datasets': [
                        {
                            'label': 'categories',
                            'tableColumn': 'category',
                            'values': [round(data.filter(category=category).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for category in categories],
                            'backgroundColor': 'rgb(255, 0, 0)',
                            'backgroundOpacity': 0.5,
                            'borderColor': 'rgb(255, 0, 0)',
                            'borderOpacity': 1,
                        },
                    ]
                }
            }
        except:
            chart_data = {}

    if chart_to_update == 'downtime trend':
        dates = data.annotate(calendar_date=TruncDate('beginning_t')).values_list('calendar_date', flat=True).distinct('calendar_date').order_by('calendar_date')
        string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

        chart_data = {
            'type': 'column',
            'data': {
                'labels': string_dates,
                'title': f"Trend prostoje na stanici {parameters['station']} (v minutách)",
                'datasets': [
                    {
                        'label': 'downtime trend',
                        'tableColumn': 'downtime',
                        'values': [round(data.filter(category=parameters['category'], station=parameters['station'], downtime=parameters['downtime'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=parameters['category'], station=parameters['station'], downtime=parameters['downtime'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                        'backgroundColor': 'rgb(255, 0, 0)',
                        'backgroundOpacity': 0.5,
                        'borderColor': 'rgb(255, 0, 0)',
                        'borderOpacity': 1,
                    },
                ]
            }
        }

    if chart_to_update == 'station trend':
        try:
            dates = data.annotate(calendar_date=TruncDate('beginning_t')).values_list('calendar_date', flat=True).distinct('calendar_date').order_by('calendar_date')
            string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

            chart_data = {
                'type': 'column',
                'data': {
                    'labels': string_dates,
                    'title': f"Trend prostojů stanice {parameters['station']} v kategorii {parameters['category']} (v minutách)",
                    'datasets': [
                        {
                            'label': 'station trend',
                            'title': f'Trend prostojů na stanici {parameters["station"]} (v minutách)',
                            'tableColumn': 'downtime',
                            'values': [round(data.filter(category=parameters['category'], station=parameters['station'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=parameters['category'], station=parameters['station'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                            'backgroundColor': 'rgb(255, 0, 0)',
                            'backgroundOpacity': 0.5,
                            'borderColor': 'rgb(255, 0, 0)',
                            'borderOpacity': 1,
                        },
                    ]
                }
            }
        except:
            chart_data = {}

    if chart_to_update == 'category trend':
        try:
            dates = data.annotate(calendar_date=TruncDate('beginning_t')).values_list('calendar_date', flat=True).distinct('calendar_date').order_by('calendar_date')
            string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

            chart_data = {
                'type': 'column',
                'data': {
                    'labels': string_dates,
                    'title': f'Trend prostojů v kategorii {parameters["category"]} (v minutách)',
                    'datasets': [
                        {
                            'label': 'station trend',
                            'tableColumn': 'downtime',
                            'values': [round(data.filter(category=parameters['category'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) if data.filter(category=parameters['category'], beginning_t__gte=date, beginning_t__lt=(date + datetime.timedelta(hours=24))).exists() else 0 for date in dates],
                            'backgroundColor': 'rgb(255, 0, 0)',
                            'backgroundOpacity': 0.5,
                            'borderColor': 'rgb(255, 0, 0)',
                            'borderOpacity': 1,
                        },
                    ]
                }
            }
        except:
            chart_data = {}


    if chart_to_update == 'downtimes':
        try:
            downtimes = [tup[0] for tup in list(data.filter(category=parameters['category'], station=parameters['station']).values('downtime').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('downtime', 'duration'))[:9]]

            chart_data = {
                'type': 'column',
                'data': {
                    'labels': downtimes,
                    'title': f'Prostoje na stanici {parameters["station"]} v kategorii {parameters["category"]} (v minutách)',
                    'datasets': [
                        {
                            'label': 'stations',
                            'tableColumn': 'downtime',
                            'values': [round(data.filter(station=parameters['station'], category=parameters['category'], downtime=downtime).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for downtime in downtimes],
                            'backgroundColor': 'rgb(255, 0, 0)',
                            'backgroundOpacity': 0.5,
                            'borderColor': 'rgb(255, 0, 0)',
                            'borderOpacity': 1,
                        },
                    ]
                }
            }
        except:
            chart_data = {}
    
    if chart_to_update == 'stations':
        try:
            stations = [tup[0] for tup in list(data.filter(category=parameters['category']).values('station').annotate(duration=Sum(ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField()))).order_by('-duration').values_list('station', 'duration'))[:9]]

            chart_data = {
                'type': 'column',
                'data': {
                    'labels': stations,
                    'title': f"Prostoje po stanicích v kategorii {parameters['category']} (v minutách)",
                    'datasets': [
                        {
                            'label': 'stations',
                            'tableColumn': 'station',
                            'values': [round(data.filter(station=station, category=parameters['category']).annotate(duration=ExpressionWrapper(F('end_t') - F('beginning_t'), output_field=DurationField())).exclude(duration__gte=datetime.timedelta(seconds=28800)).aggregate(duration_sum=Sum('duration'))['duration_sum'].total_seconds() / 60) for station in stations],
                            'backgroundColor': 'rgb(255, 0, 0)',
                            'backgroundOpacity': 0.5,
                            'borderColor': 'rgb(255, 0, 0)',
                            'borderOpacity': 1,
                        },
                    ]
                }
            }
        except:
            chart_data = {}

    

    return JsonResponse(chart_data)