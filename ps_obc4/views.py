from django.http import JsonResponse
from django.shortcuts import render
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
import json
import datetime


def svg_charts(request):
    date_to = datetime.datetime.now()
    date_from = date_to - datetime.timedelta(days=10)

    shifts_count = 3

    shift_model = {
        2: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 'afternoon_shift_hours': [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5], 'next_day': 18},
        3: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13], 'afternoon_shift_hours': [14, 15, 16, 17, 18, 19, 20, 21], 'next_day': 22}
    }

    #### data, ktore maju dva vystupy, category a duration. To bude vsetko technical
    ### 0 text alarmu
    ### 1 stanice
    ### 2 trvani
    ### 3 smena
    ### 4 den smeny

    data_query = f"""WITH cte AS (SELECT AlarmTextCz AS AlarmText, IDStation AS Station, DATEDIFF(second, TimeStampAlarmStart, TimeStampAlarmEnd) AS Duration, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) IN ({str(shift_model[shifts_count]['morning_shift_hours']).strip('[').strip(']')}) THEN 'R' WHEN DATEPART(HOUR, TimeStampAlarmStart) IN ({str(shift_model[shifts_count]['afternoon_shift_hours']).strip('[').strip(']')}) THEN 'O' ELSE 'N' END AS Shift, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= {shift_model[shifts_count]['next_day']} THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS Date)) ELSE CAST(TimeStampAlarmStart AS Date) END AS ShiftDate
    
    FROM [OBC_04].[dbo].[AlarmsAll] WHERE TimeStampAlarmStart >= '{(date_from - datetime.timedelta(days = 1)).date()}' AND AlarmType = 1 AND LineMode = 1 AND TimeStampAlarmEnd IS NOT NULL)
    
    SELECT AlarmText, Station, Duration / 60, Shift, ShiftDate
    FROM cte
    WHERE ShiftDate >= '{date_from.date()}'
    AND Duration / 60 < 1440
    ORDER BY ShiftDate
    """

    with connections['jirkal_117'].cursor() as cursor:
        cursor.execute(data_query)

        data = cursor.fetchall()

    categories = ['Technical downtime / Technický prostoj', sum([tup[2] for tup in data])]

    chart_data_categories = {
        'type': 'column',
        'data': {
            'labels': [categories[0]],
            'title': 'Prostoje po kategoriích (v minutách)',
            'datasets': [
                {
                    'label': 'categories',
                    'tableColumn': 'category',
                    'values': [categories[1]],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    ### toto bude chciet refactoring, pretoze dates nemusi obsahovat vsetky kalendarne datumy
    ### mozno postaci vygenerovat sekvenciu a potom pouzivat get('datum', 0)? 
    dates = sorted(list(set([tup[4] for tup in data])))

    string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

    dates_dict = {x: 0 for _, _, _, _, x in data} # not proud of _

    for _, _, duration, _, date in data:
        dates_dict[date] += duration

    chart_data_trend_categories = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostojů v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'categories trend',
                    'tableColumn': 'category',
                    'values': [dates_dict.get(d, '0') for d in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    stations_dict = {x: 0 for _, x, _, _, _ in data}

    for _, station, duration, _, _ in data:
        stations_dict[station] += duration

    sorted_stations = sorted(stations_dict.items(), key=lambda t: t[1], reverse=True)[:9]

    chart_data_stations = {
        'type': 'column',
        'data': {
            'labels': [f"ST{tup[0]}" for tup in sorted_stations],
            'title': f'Prostoje po stanicích v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations',
                    'tableColumn': 'station',
                    'values': [tup[1] for tup in sorted_stations],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    station_downtimes = list(filter(lambda x: x[1] == sorted_stations[0][0], data))

    station_trend_dict = {x: 0 for _, _, _, _, x in station_downtimes}

    for _, _, duration, _, d in station_downtimes:
        station_trend_dict[d] += duration

    chart_data_trend_stations = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostojů na stanici {sorted_stations[0][0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations trend',
                    'tableColumn': 'category',
                    'values': [station_trend_dict.get(d, '0') for d in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    downtimes_dict = {x: 0 for x, station, _, _, _ in data if station == sorted_stations[0][0]}

    for downtime, station, duration, _, _ in data:
        if station == sorted_stations[0][0]:
            try:
                downtimes_dict[downtime] += duration
            except KeyError:
                pass

    sorted_downtimes = sorted(downtimes_dict.items(), key=lambda t: t[1], reverse=True)[:9]

    chart_data_downtimes = {
        'type': 'column',
        'data': {
            'labels': [tup[0] for tup in sorted_downtimes],
            'title': f'Prostoje stanice {sorted_stations[0][0]} v kategorii {categories[0]} (v minutách)',
            'datasets': [
                {
                    'label': 'stations',
                    'tableColumn': 'downtime',
                    'values': [tup[1] for tup in sorted_downtimes],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }

    station_downtime_downtimes = list(filter(lambda x: x[1] == sorted_stations[0][0] and x[0] == sorted_downtimes[0][0], data))

    station_downtime_trend_dict = {x: 0 for _, _, _, _, x in station_downtime_downtimes}

    for _, _, duration, _, d in station_downtime_downtimes:
        station_downtime_trend_dict[d] += duration

    chart_data_trend_downtimes = {
        'type': 'column',
        'data': {
            'labels': string_dates,
            'title': f'Trend prostoje na stanici {sorted_stations[0][0]} (v minutách)',
            'datasets': [
                {
                    'label': 'downtimes trend',
                    'tableColumn': 'downtime',
                    'values': [station_downtime_trend_dict.get(d, '0') for d in dates],
                    'backgroundColor': 'rgb(255, 0, 0)',
                    'backgroundOpacity': 0.5,
                    'borderColor': 'rgb(255, 0, 0)',
                    'borderOpacity': 1,
                },
            ]
        }
    }
 
    return render(request, 'obc4/ps_svg_charts.html', {'data_categories': chart_data_categories, 'data_stations': chart_data_stations, 'data_downtimes': chart_data_downtimes, 'data_trend_categories': chart_data_trend_categories, 'data_trend_stations': chart_data_trend_stations, 'data_trend_downtimes': chart_data_trend_downtimes})


@csrf_exempt
def svg_charts_fetch(request):
    parameters = json.loads(request.body)

    date_to = datetime.datetime.strptime(parameters["date_to"], "%a, %d %b %Y %H:%M:%S %Z")
    date_from = datetime.datetime.strptime(parameters["date_from"], "%a, %d %b %Y %H:%M:%S %Z")
    shifts = parameters.get('shifts', ['R', 'O', 'N'])

    shifts_count = 3

    shift_model = {
        2: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 'afternoon_shift_hours': [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5], 'next_day': 18},
        3: {'morning_shift_hours': [6, 7, 8, 9, 10, 11, 12, 13], 'afternoon_shift_hours': [14, 15, 16, 17, 18, 19, 20, 21], 'next_day': 22}
    }

    data_query = f"""WITH cte AS (SELECT AlarmTextCz AS AlarmText, IDStation AS Station, DATEDIFF(second, TimeStampAlarmStart, TimeStampAlarmEnd) AS Duration, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) IN ({str(shift_model[shifts_count]['morning_shift_hours']).strip('[').strip(']')}) THEN 'R' WHEN DATEPART(HOUR, TimeStampAlarmStart) IN ({str(shift_model[shifts_count]['afternoon_shift_hours']).strip('[').strip(']')}) THEN 'O' ELSE 'N' END AS Shift, CASE WHEN DATEPART(HOUR, TimeStampAlarmStart) >= {shift_model[shifts_count]['next_day']} THEN DATEADD(day, 1, CAST(TimeStampAlarmStart AS Date)) ELSE CAST(TimeStampAlarmStart AS Date) END AS ShiftDate
    
    FROM [OBC_04].[dbo].[AlarmsAll] WHERE TimeStampAlarmStart >= '{(date_from - datetime.timedelta(days = 1)).date()}' AND AlarmType = 1 AND LineMode = 1 AND TimeStampAlarmEnd IS NOT NULL)
    
    SELECT AlarmText, Station, Duration / 60, Shift, ShiftDate
    FROM cte
    WHERE ShiftDate >= '{date_from.date()}'
    AND ShiftDate <= '{date_to.date()}'
    AND Duration / 60 < 1440
    AND Shift IN ({str(shifts).strip(']').strip('[')})
    ORDER BY ShiftDate
    """

    with connections['jirkal_117'].cursor() as cursor:
        cursor.execute(data_query)

        data = cursor.fetchall()

    chart_to_update = parameters['chart_to_update']

    if chart_to_update == 'categories':
        categories = ['Technical downtime / Technický prostoj', sum([tup[2] for tup in data])]

        chart_data = {
            'type': 'column',
            'data': {
                'labels': [categories[0]],
                'title': 'Prostoje po kategoriích (v minutách)',
                'datasets': [
                    {
                        'label': 'categories',
                        'tableColumn': 'category',
                        'values': [categories[1]],
                        'backgroundColor': 'rgb(255, 0, 0)',
                        'backgroundOpacity': 0.5,
                        'borderColor': 'rgb(255, 0, 0)',
                        'borderOpacity': 1,
                    },
                ]
            }
        }
    # except:
    #     chart_data = {}

    if chart_to_update == 'downtime trend':
        dates = sorted(list(set([tup[4] for tup in data])))
        string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

        station_downtime_downtimes = list(filter(lambda x: x[1] == int(parameters['station']) and x[0] == parameters['downtime'], data))

        station_downtime_trend_dict = {x: 0 for _, _, _, _, x in station_downtime_downtimes}

        for _, _, duration, _, d in station_downtime_downtimes:
            station_downtime_trend_dict[d] += duration

        chart_data = {
            'type': 'column',
            'data': {
                'labels': string_dates,
                'title': f"Trend prostoje na stanici {parameters['station']} (v minutách)",
                'datasets': [
                    {
                        'label': 'downtime trend',
                        'tableColumn': 'downtime',
                        'values': [station_downtime_trend_dict.get(d, 0) for d in dates],
                        'backgroundColor': 'rgb(255, 0, 0)',
                        'backgroundOpacity': 0.5,
                        'borderColor': 'rgb(255, 0, 0)',
                        'borderOpacity': 1,
                    },
                ]
            }
        }

    if chart_to_update == 'station trend':

        station_downtimes = list(filter(lambda x: x[1] == int(parameters['station']), data))

        station_trend_dict = {x: 0 for _, _, _, _, x in station_downtimes}

        for _, _, duration, _, d in station_downtimes:
            station_trend_dict[d] += duration

        try:
            dates = sorted(list(set([tup[4] for tup in data])))
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
                            'values': [station_trend_dict.get(d, 0) for d in dates],
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
        dates = sorted(list(set([tup[4] for tup in data])))
        string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

        dates_dict = {x: 0 for _, _, _, _, x in data} # not proud of _

        for _, _, duration, _, d in data:
            dates_dict[d] += duration

        try:
            chart_data = {
                'type': 'column',
                'data': {
                    'labels': string_dates,
                    'title': f'Trend prostojů v kategorii {parameters["category"]} (v minutách)',
                    'datasets': [
                        {
                            'label': 'station trend',
                            'tableColumn': 'downtime',
                            'values': [dates_dict.get(d, 0) for d in dates],
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

        downtimes_dict = {x: 0 for x, station, _, _, _ in data if station == int(parameters['station'])}

        for downtime, station, duration, _, _ in data:
            if station == int(parameters['station']):
                try:
                    downtimes_dict[downtime] += duration
                except KeyError:
                    pass

        sorted_downtimes = sorted(downtimes_dict.items(), key=lambda t: t[1], reverse=True)[:9]

        dates = sorted(list(set([tup[4] for tup in data])))
        string_dates = [datetime.datetime.strftime(date, "%m-%d") for date in dates]

        try:
            chart_data = {
                'type': 'column',
                'data': {
                    'labels': [tup[0] for tup in sorted_downtimes],
                    'title': f'Prostoje na stanici {parameters["station"]} v kategorii {parameters["category"]} (v minutách)',
                    'datasets': [
                        {
                            'label': 'stations',
                            'tableColumn': 'downtime',
                            'values': [tup[1] for tup in sorted_downtimes],
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
        stations_dict = {x: 0 for _, x, _, _, _ in data}

        for _, station, duration, _, _ in data:
            stations_dict[station] += duration

        sorted_stations = sorted(stations_dict.items(), key=lambda t: t[1], reverse=True)[:9]
        
        try:
            chart_data = {
                'type': 'column',
                'data': {
                    'labels': [f"ST{tup[0]}" for tup in sorted_stations],
                    'title': f"Prostoje po stanicích v kategorii {parameters['category']} (v minutách)",
                    'datasets': [
                        {
                            'label': 'stations',
                            'tableColumn': 'station',
                            'values': [tup[1] for tup in sorted_stations],
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