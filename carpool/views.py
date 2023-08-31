from multiprocessing import pool
from re import L
from django.shortcuts import render, redirect
import math
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import calendar
import datetime
import isoweek
from .models import Car, Referent, Reservation, PickupReport, CarLoan, ReturnReport, CarDamage, CarRepair, CarProfile, PickupImage, DamageReport
from django.http import JsonResponse, HttpResponse
import json
from django.core.files.storage import FileSystemStorage
from unidecode import unidecode
from .utils import sendAppointment
from django.contrib.auth.models import User
import qrcode
from PIL import Image

import os
import imaplib
import email
import smtplib

def show_car(request):
    license_plate = request.GET.get('license_plate')
    header_object = Car.objects.first()
    header = header_object.get_header()
    car_information = list(Car.objects.filter(car_license_plate = license_plate).values_list(*header))
    car_id = car_information[0][0]
    car_accident = list(CarDamage.objects.filter(accident_car_id = car_id).values_list('accident_description', 'accident_date', 'accident_person_id', 'carloan_id', 'urls', 'driver_role').order_by('-accident_date'))
    #Nahradit accident_person_id za jmeno
    header_object = PickupReport.objects.first()
    header = header_object.get_header()
    car_pickupreport = list(PickupReport.objects.filter(pickup_car_id = car_id).values_list(*header).order_by('-pickup_datetime'))
    #pickup_car_id nahradit za jmeno
    header_object = Reservation.objects.first()
    header = header_object.get_header()
    car_reservation = list(Reservation.objects.filter(reserved_car_id = car_id).values_list(*header).order_by('-reservation_datetime_start'))
    #nahradit id creatora za jmeno
    car_accident_dict = {}

    for i in range(0, len(car_accident)):
        car_accident_dict[i] = []
        for record in car_accident[i]:
            if type(record) == datetime.date:
                record = record.strftime('%Y-%m-%d')
            car_accident_dict[i].append(record)

    car_pickupreport_dict = {}
    for i in range(0, len(car_pickupreport)):
        car_pickupreport_dict[i] = []
        for record in car_pickupreport[i]:
            if type(record) == datetime.datetime:
                record = record.strftime('%Y-%m-%d %H:%M')
            car_pickupreport_dict[i].append(record)

    car_reservation_dict = {}
    for i in range(0, len(car_reservation)):
        car_reservation_dict[i] = []
        for record in car_reservation[i]:
            if type(record) == datetime.datetime:
                record = record.strftime('%Y-%m-%d %H:%M')
            if type(record) == bool:
                if record == True or record == "true":
                    record = "True"
                else:
                    record = "False"
            car_reservation_dict[i].append(record)

    context = { 'car_information': car_information,
                'car_accident': car_accident_dict,
                'car_pickupreport': car_pickupreport_dict,
                'car_reservation': car_reservation_dict}
    return render(request, 'show_car.html', context)


def create_qrcode(license_plate):
    all = False
    if all:
        cars = Car.objects.order_by('car_license_plate').exclude(car_license_plate=None).values_list('car_license_plate', flat=True)
        for license_plate in cars:
            input_data = f'http://10.49.34.115/carpool/show_car?license_plate={license_plate}'
            qr = qrcode.QRCode(
                    version=1,
                    box_size=10,
                    border=5)
            qr.add_data(input_data)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            img.save(f'/home/vajdap/Knorr/media/qrcodes/{license_plate}.png')
    else:
        input_data = f'http://10.49.34.115/carpool/show_car?license_plate={license_plate}'
        qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5)

        qr.add_data(input_data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img.save(f'media/qrcodes/{license_plate}.png')


@login_required
def carpool_home(request):

    if CarProfile.objects.filter(user=request.user).exists():
        pass
    else:
        CarProfile.objects.create(user=request.user)

    context = {
    }

    return render(request, 'carpool_home_new.html', context)


@csrf_exempt
def add_car(request):

    if request.method == "POST":
        request_data = json.loads(request.body)

        print(request_data)

        license_plate = request_data['license_plate'].replace("-","").upper()
        car_manufacturer = request_data['car_manufacturer']
        car_make = request_data['car_make']
        technical_certificate = request_data['technical_certificate']
        shell_number = request_data['shell_number']
        pin = request_data['pin']
        next_service_kms = request_data['next_service_kms']
        next_service_date = request_data['next_service_date']
        kms_limit = request_data['kms_limit']
        active = True if request_data['active'] == 'on' else False
        pool_car = True

        Car.objects.get_or_create(car_license_plate=license_plate, defaults={'car_manufacturer': car_manufacturer, 'car_make': car_make, 'technical_certificate': technical_certificate, 'shell_number': shell_number, 'pin': pin, 'next_service_date': next_service_date, 'next_service_kms': next_service_kms, 'kms_limit': kms_limit, 'active': active, 'pool_car': pool_car})

        create_qrcode(license_plate.upper())

        return JsonResponse({'status': 'okay'})


def show_cars(request):
    context = {}

    pool_cars = Car.objects.filter(pool_car=True).order_by('car_license_plate').exclude(car_license_plate=None).exclude(deleted=True)

    context.update({
        'pool_cars': pool_cars,
    })

    if request.method == "POST":

        carObject, created = Car.objects.get_or_create(car_license_plate=request.POST.get('license_plate'))

        for key, value in dict(request.POST).items():
            if key not in ['car_owner', 'csrf_token', 'pool-car', 'csrfmiddlewaretoken']:
                try:
                    setattr(carObject, key, value[0]) if value[0] else setattr(carObject, key, None)
                except:
                    setattr(carObject, key, None)
            if key == 'pool-car':
                if value[0] == 'pool':
                    carObject.pool_car = True
                    carObject.manager_car = False
                else:
                    carObject.pool_car = False
                    carObject.manager_car = True
            if key in ['car_owner']:
                try:
                    setattr(carObject, key, User.objects.get(first_name=value[0].split()[0], last_name=value[0].split()[1]))
                except:
                    setattr(carObject, key, None)
        
        carObject.save()
        
    return render(request, 'show_cars.html', context)


@csrf_exempt
@login_required
def create_reservation(request, year, week, car, day, start):
    context = {}

    datetime_string = str(year) + '-' + str(week-1) + '-' + str(day) + ' ' + str(f'{start:02}')

    datetime_start = datetime.datetime.strptime(datetime_string, '%Y-%W-%u %H') + datetime.timedelta(days=7)

    carObject = Car.objects.filter(pool_car=True).exclude(active=False).exclude(deleted=True).order_by('car_license_plate')[car-1]

    is_special = request.user.is_superuser

    context.update({
        'start': datetime_start.strftime("%Y-%m-%dT%H:%M"),
        'car': carObject,
        'users': User.objects.all().order_by('last_name'),
        'is_special': is_special,
    })

    if request.method == "POST":
        
        datetime_start = request.POST.get('starting-date')
        datetime_end = request.POST.get('destination-date')
        reservation_user_string = request.POST.get('user').split(" ")

        reservationObject = Reservation.objects.create(
            reservation_datetime_start = datetime_start, 
            reservation_datetime_end = datetime_end, 
            reserved_car = carObject, 
            reservation_user = User.objects.get(last_name=reservation_user_string[1], first_name=reservation_user_string[0]),
            destination = request.POST.get('destination'),
            kilometres = request.POST.get('kilometres'),
            is_special = is_special,
        )

        sendAppointment(attendee=reservationObject.reservation_user.email, start_datetime=reservationObject.reservation_datetime_start, end_datetime=reservationObject.reservation_datetime_end, event_id=reservationObject.id)

        return JsonResponse({'status': 'ok'})


    return render(request, 'create_reservation.html', context)


@login_required
@csrf_exempt
def edit_reservation(request, reservation_id):
    context = {}

    reservationId = reservation_id.replace("reservation","")

    reservationObject = Reservation.objects.get(id=reservationId)

    if reservationObject.reservation_user == request.user or request.user.carprofile.is_superuser:
        can_edit = True
    else:
        can_edit = False

    context.update({
        'reservation': reservationObject,
        'user_can_edit': can_edit,
        'users': User.objects.all().order_by('last_name'),
    })

    if request.method == "POST":
        if request.POST.get('Action') == "Smazat":
            sendAppointment(attendee=request.user.email, start_datetime=str(reservationObject.reservation_datetime_start), end_datetime=str(reservationObject.reservation_datetime_end), event_id=reservationObject.id, canceled=True)
            try:
                sendAppointment(attendee=reservationObject.reservation_user.email, start_datetime=str(reservationObject.reservation_datetime_start), end_datetime=str(reservationObject.reservation_datetime_end), event_id=reservationObject.id, canceled=True)
            except:
                pass

            reservationObject.delete()

        else:
            user_string = request.POST.get('user').split(" ")
            reservationObject.reservation_datetime_start = datetime.datetime.strptime(request.POST.get('starting-date').replace('T', ' '), "%Y-%m-%d %H:%M")
            reservationObject.reservation_datetime_end = datetime.datetime.strptime(request.POST.get('destination-date').replace('T', ' '), "%Y-%m-%d %H:%M")
            reservationObject.destination = request.POST.get('destination')
            reservationObject.reservation_user = User.objects.get(last_name=user_string[1], first_name=user_string[0])
            reservationObject.save()

            sendAppointment(attendee=request.user.email, start_datetime=str(reservationObject.reservation_datetime_start), end_datetime=str(reservationObject.reservation_datetime_end), event_id=reservationObject.id)

            context.update({
                'reservation': reservationObject,
            })

        return JsonResponse({'status': 'okay'})

    return render(request, 'edit_reservation.html', context)

@login_required
def create_carloan(request):
    context = {}
    reservationObjects = Reservation.objects.filter(reservation_user=request.user, reservation_used=False)

    context.update({
        'reservations': reservationObjects,
    })
    
    return render(request, 'create_carloan.html', context)


@login_required
@csrf_exempt
def create_carloan_form(request, reservation_id):
    context = {}
    reservationObject = Reservation.objects.get(id=reservation_id)
    fieldsInterior = [
        ('vehicle-cleanness', 'Čistota vozu'),
        ('carpets', 'Stav koberečků'),
        ('seats', 'Stav sedadel'),
        ('trunk', 'Stav zavazadlového prostoru'),
        ('mandatory-equipment', 'Povinná výbava'),
        ('interior-other', 'Ostatní'),
        ('tank-status', 'Stav nádrže'),
        ('tachometer-value', 'Stav tachometru'),
        ('active-warning', 'Kontrolka servisu'),
    ]

    fieldsExterior = [
        ('front-bumper', 'Přední nárazník'),
        ('rear-bumper', 'Zadní nárazník'),
        ('lights', 'Stav světel'),
        ('car-body', 'Stav karoserie'),
        ('tires', 'Stav pneumatik'),
        ('windshield', 'Stav čelního skla'),
        ('washer-fluid', 'Kapalina v ostřikovačích'),
        ('exterior-other', 'Ostatní'),
    ]

    carloanObject, created = CarLoan.objects.get_or_create(reservation=reservationObject)

    context.update({
        'reservation': reservationObject,
        'fieldsInterior': fieldsInterior,
        'fieldsExterior': fieldsExterior,
    })

    if request.method == "POST":
        carObject = reservationObject.reserved_car

        carloanObject.car_loaner = reservationObject.reservation_user

        carloanObject.carloan_start = request.POST.get('carloan_pickup_time')
        carloanObject.carloan_end = request.POST.get('carloan_end')
        carloanObject.reservation.reserved_car.car_mileage = int(request.POST.get('tachometer-value'))
        carloanObject.reservation.reserved_car.save()
        carloanObject.save()

        reservationObject.reservation_used = True
        reservationObject.save()

        update_dict = {}

        for tup in fieldsExterior:
            update_dict[tup[0].replace("-", "_")] = True if request.POST.get(tup[0], "") == 'true' else (False if request.POST.get(tup[0], "") == 'false' else request.POST.get(tup[0], ""))

        for tup in fieldsInterior:
            update_dict[tup[0].replace("-", "_")] = True if request.POST.get(tup[0], "") == 'true' else (False if request.POST.get(tup[0], "") == 'false' else request.POST.get(tup[0], ""))

        update_dict['pickup_person'] = reservationObject.reservation_user
        update_dict['pickup_car'] = reservationObject.reserved_car
        update_dict['pickup_datetime'] = request.POST['carloan_pickup_time']
        
        pickUpReportObject, created = PickupReport.objects.update_or_create(carloan=carloanObject, defaults=update_dict)

        for obj in request.FILES:
            field_name = request.FILES[obj].name.split('camera-upload-')[1].split('_')[0]
            image = PickupImage.objects.create(image=request.FILES[obj], pickup_report=pickUpReportObject, field=field_name)
        
        context.update({
            'uploaded': True,
        })

        return JsonResponse({'resp': 'okay'})
        
    carloanObjects = CarLoan.objects.filter(reservation__reserved_car=reservationObject.reserved_car)

    context.update({
        'historical_carloans': carloanObjects,
    })

    return render(request, 'create_carloan_form.html', context)


@login_required
def carpool_calendar(request, year=datetime.date.today().year, month=None, week=None):

    if week is None:
        week=datetime.date.today().isocalendar()[1]

    if month is None:
        month=datetime.date.today().month

    if week == 0:
        week = 52
        year = year - 1

    if week == 53:
        week = 1
        year = year + 1

    context = {}
    list_of_dicts = []

    c = calendar.Calendar()
    if month == datetime.date.today().month and week == datetime.date.today().isocalendar()[1]:
        for week_iter in c.monthdatescalendar(year, month):
            for day in week_iter:
                if day == datetime.date.today():
                    context.update({'week': week_iter})
                    break
    else:
        fiction_monday = c.yeardatescalendar(year)[0][0][0][0] + datetime.timedelta(days=7*week)
        for month in c.yeardatescalendar(year, width=12)[0]:
            for week_iter in month:
                for day in week_iter:
                    if day == fiction_monday:
                        context.update({'week': week_iter})
                        break

        context.update({
            'last_week': isLastWeek(year, week),
        })

    list_of_cars = Car.objects.filter(pool_car=True).exclude(deleted=True).exclude(active=False).order_by('car_license_plate')

    reservationObjects_query1 = Reservation.objects.filter(reservation_datetime_start__lte=context['week'][6] + datetime.timedelta(days=1), reservation_datetime_start__gte=context['week'][0]).exclude(reserved_car__manager_car=True).exclude(reserved_car__deleted=True).exclude(reserved_car__active=False).exclude(reserved_car__isnull=True)
    reservationObjects_query2 = Reservation.objects.filter(reservation_datetime_start__lt=context['week'][0], reservation_datetime_end__gte=context['week'][0]).exclude(reserved_car__manager_car=True).exclude(reserved_car__deleted=True).exclude(reserved_car__active=False).exclude(reserved_car__isnull=True)

    reservationObjects = reservationObjects_query1.union(reservationObjects_query2)
    
    for reservationObject in reservationObjects:
        from_history = False # If the reservation started in the week(s) before actual week, this will turn True
        fictional_start = False
        fictional_end = False

        car_position = list(list_of_cars).index(reservationObject.reserved_car)

        start_day_date = reservationObject.reservation_datetime_start.date()

        try:
            start_day_position = context['week'].index(start_day_date)
        except:
            start_day_position = 0
            from_history = True

        if reservationObject.reservation_datetime_end.hour > 17:
            fictional_end = reservationObject.reservation_datetime_end.replace(hour=17)

        if reservationObject.reservation_datetime_end.hour < 8:
            fictional_end = reservationObject.reservation_datetime_end.replace(hour=8)

        if reservationObject.reservation_datetime_start.hour < 8:
            fictional_start = reservationObject.reservation_datetime_start.replace(hour=8, minute=0, second=0)

        duration = (fictional_end if fictional_end else reservationObject.reservation_datetime_end) - (fictional_start if fictional_start else reservationObject.reservation_datetime_start)

        duration_in_hours = duration.total_seconds()/3600
        duration_in_days = math.floor(duration_in_hours / 24)

        rest_in_hours = duration_in_hours % 24

        if rest_in_hours > 9:
            rest_in_hours = 9

        duration_in_hours = (duration_in_days * 9) + (rest_in_hours)

        start_of_week_datetime = datetime.datetime(year=context['week'][0].year, month=context['week'][0].month, day=context['week'][0].day).replace(tzinfo=None)

        if from_history:
            duration_in_hours_in_actual_week = (reservationObject.reservation_datetime_end.replace(tzinfo=None) - start_of_week_datetime).total_seconds()/3600
            duration_in_days_in_actual_week = math.floor(duration_in_hours_in_actual_week / 24)
            try:
                hours_modulo = int(duration_in_hours_in_actual_week) % int(duration_in_days_in_actual_week * 24)
            except:
                hours_modulo = duration_in_hours_in_actual_week - 8
            duration = (duration_in_days_in_actual_week * 9) + (hours_modulo - 8 if hours_modulo > 8 else hours_modulo)
            if fictional_end:
                duration -= hours_modulo - fictional_end.hour

        else:
            duration = duration_in_hours
        
        if duration + (start_day_position * 9) > 63:
            # duration = 63 - (start_day_position * 9) - ((fictional_start if fictional_start else reservationObject.reservation_datetime_start - (fictional_start if fictional_start else reservationObject.reservation_datetime_start).replace(hour=8))).seconds / 3600

            duration = 63

        res_dict = {}
        res_dict['duration'] = duration
        res_dict['id'] = reservationObject.id

        if reservationObject.repair_reservation:
            res_dict['hover_info'] = '<div class="carpool-calendar-hover-message"><div>' + 'Servis' + '</div></div>'
        else:
            res_dict['hover_info'] = '<div class="carpool-calendar-hover-message"><div>' + reservationObject.reservation_user.first_name + ' ' + str(reservationObject.reservation_user.last_name) + '<br />' + reservationObject.destination + '</div></div>'
        
        res_dict['start_id'] = str(car_position + 1) + '-' + str(start_day_position + 1) + '-' + str(int(fictional_start.hour if fictional_start else (reservationObject.reservation_datetime_start.hour if not from_history else 8)))
        res_dict['hover_info_plain_text'] = str(reservationObject.reservation_datetime_start) + ' - ' + str(reservationObject.reservation_datetime_end)

        list_of_dicts.append(res_dict)


    context.update({
        'list_of_dicts': list_of_dicts,
        'list_of_cars': list_of_cars,
        'year': year,
        'week_n': week,
    })

    if request.method == "POST":
        pass

    return render(request, 'carpool_calendar.html', context)


def isLastWeek(source_year, source_week):
    if isoweek.Week.last_week_of_year(source_year).week == source_week:
        return True


@csrf_exempt
def validate_car_availability(request):

    request_data = json.loads(request.body)
    car = Car.objects.get(car_license_plate = request_data['license-plate'])

    if 'reservation-id' in request_data:
        conflicting_reservation = Reservation.objects.filter(reserved_car = car, reservation_datetime_start__gte = request_data['start'], reservation_datetime_start__lte = request_data['end']).exclude(id = request_data['reservation-id']).exists()
    else:
        conflicting_reservation = Reservation.objects.filter(reserved_car = car, reservation_datetime_start__gte = request_data['start'], reservation_datetime_start__lte = request_data['end']).exists()

    if conflicting_reservation:
        return JsonResponse({'status': 'unavailable', 'reservations': list(Reservation.objects.filter(reserved_car = car, reservation_datetime_start__gte = request_data['start'], reservation_datetime_end__lte = request_data['end']).values())})
    else:
        return JsonResponse({'status': 'available'})


@login_required
def return_car(request):
    context = {}

    activeCarloanObjects = CarLoan.objects.filter(reservation__reservation_user = request.user, closed=False)

    context.update({
        'active_carloans': activeCarloanObjects,
    })

    return render(request, 'return_car.html', context)


@csrf_exempt
def return_car_form(request, carloan_id):
    context = {}

    carloanObject = CarLoan.objects.get(id=carloan_id)
    carloanObjects = CarLoan.objects.filter(reservation__reserved_car=carloanObject.reservation.reserved_car)

    context.update({
        'carloan_object': carloanObject,
        'historical_carloans': carloanObjects,
    })

    if request.method == "POST":

        request_data = json.loads(request.body)

        carObject = carloanObject.reservation.reserved_car

        returnReportObject, created = ReturnReport.objects.update_or_create(carloan=carloanObject, defaults={'carloan': carloanObject, 'return_datetime': request_data['carloan-return-time'], 'tachometer_value': request_data['tachometer-value'], 'notes': request_data.get('notes', ''), 'tank_status': request_data['tank-status']})
        for key, value in request_data['dictionary-damage-descriptions'].items():
            returnDamageReportObject, created = DamageReport.objects.update_or_create(carloan=carloanObject, part_damaged=key, defaults={'carloan': carloanObject, 'car_mileage': int(request_data['tachometer-value']), 'reservation_datetime_start': request_data['carloan-start'], 'reservation_datetime_end': request_data['carloan-end'], 'return_datetime': request_data['carloan-return-time'], 'part_damaged': key, 'description': value})

        carObject.car_mileage = int(request_data['tachometer-value'])
        carObject.save()

        carloanObject.closed = True
        carloanObject.save()

        return JsonResponse({'status': 'okay'})

    return render(request, 'return_car_form.html', context)

@login_required
def show_accident_reports_v2(request):
    context = {}
    
    try:
        carpool_user = CarProfile.objects.get(user=request.user)
    except:
        carpool_user = False

    context.update({
        'carpool_user': carpool_user,
    })

    accident_reports = CarDamage.objects.all()
    open_accidents = accident_reports.filter(repair_created=False)
    closed_accidents = accident_reports.filter(repair_created=True)
    carloans = CarLoan.objects.filter(carloan_end__lte=datetime.datetime.now())

    context.update({
        'accident_reports': accident_reports,
        'open_accidents': open_accidents,
        'closed_accidents': closed_accidents,
        'carloans': carloans,
    })

    return render(request, 'show_accident_reports_v2.html', context)

@login_required
def show_accident_reports(request):
    context = {}
    
    try:
        carpool_user = CarProfile.objects.get(user=request.user)
    except:
        carpool_user = False

    context.update({
        'carpool_user': carpool_user,
    })
    carloan_ids = list(DamageReport.objects.filter(repair_created = False).values_list('carloan_id', flat=True).distinct())
    carloan_descriptions = list(CarLoan.objects.filter(id__in = carloan_ids).values('id', 'reservation_id', 'reservation__reservation_user__id'))
    open_accidents = {}
    for carloan_description in carloan_descriptions:
        open_accidents[carloan_description['id']] = []
        reservation_info = list(Reservation.objects.filter(id = carloan_description['reservation_id']).values('reservation_datetime_start', 'reservation_datetime_end', 'destination', 'reserved_car__id'))
        user_info = list(User.objects.filter(id = carloan_description['reservation__reservation_user__id']).values('first_name', 'last_name'))
        car_info = list(Car.objects.filter(id = reservation_info[0]['reserved_car__id']).values('car_manufacturer', 'car_make', 'car_license_plate'))
        damage_reports = list(DamageReport.objects.filter(repair_created = False, carloan_id = carloan_description['id']).values('part_damaged', 'description'))
        open_accidents[carloan_description['id']].append([reservation_info[0]['reservation_datetime_start'].strftime("%d/%m/%Y, %H:%M:%S"), reservation_info[0]['reservation_datetime_end'].strftime("%d/%m/%Y, %H:%M:%S"), reservation_info[0]['destination'], user_info[0]['first_name'], user_info[0]['last_name'], car_info[0]['car_manufacturer'], car_info[0]['car_make'], car_info[0]['car_license_plate']])
        open_accidents[carloan_description['id']].append(damage_reports)
        png_list = [file for file in os.listdir('/home/vajdap/Knorr/media/carpool/accident_images') if file.startswith(str(carloan_description['id']))]
        open_accidents[carloan_description['id']].append(png_list)
    context.update({
        'open_accidents': open_accidents,
    })


    return render(request, 'show_accident_reports.html', context)

def get_carloans(request):
    carloans = CarLoan.objects.all()

    excluded_ids = []

    for carloan in carloans:
        if carloan.CarDamage_set.all().count() > 0:
            excluded_ids.append(carloan.id)

    carloans.exclude(id__in=excluded_ids)

    list_of_passing_data_dicts = []


    for carloan in carloans:
        passing_data = {}
        passing_data['carloan_id'] = carloan.id
        passing_data['carloan_car_license_plate'] = carloan.reservation.reserved_car.car_license_plate
        passing_data['carloan_start'] = datetime.datetime.strftime(carloan.carloan_start, "%Y-%m-%d")
        passing_data['carloan_end'] =  datetime.datetime.strftime(carloan.carloan_end, "%Y-%m-%d")

        list_of_passing_data_dicts.append(passing_data)

    return JsonResponse(list_of_passing_data_dicts, safe=False)


@csrf_exempt
def get_car_data(request):

    req = json.loads(request.body)

    carObject = Car.objects.get(car_license_plate=req['license-plate'])

    fields = [field.name for field in Car._meta.get_fields()]

    resp = {}

    for field in fields:
        try:
            resp[field] = getattr(carObject, field)
        except:
            pass

    return JsonResponse(resp)


def create_repair_from_accident(request, accident_report_id):
    
    context = {}

    CarDamageObject = CarDamage.objects.get(id=accident_report_id)
    carloanObject = CarDamageObject.carloan

    context.update({
        'accident_report': CarDamageObject,
    })

    if request.method == "POST":

        updates = {}

        carObject = Car.objects.get(car_license_plate=request.POST.get('car_license_plate'))
        updates['car'] = carObject
        updates['caused_by_accident'] = True
        updates['caused_by_wear'] = False
        updates['carloan'] = carloanObject

        if request.POST.get('repair_start'):
            updates['repair_start'] = request.POST.get('repair_start')

        if request.POST.get('cost_estimate'):
            updates['cost_estimate'] = request.POST.get('cost_estimate')

        if request.POST.get('repair_end'):
            updates['repair_end'] = request.POST.get('repair_end')

        if request.POST.get('end_estimate'):
            updates['end_estimate'] = request.POST.get('end_estimate')

        if request.POST.get('repair_cost'):
            updates['repair_cost'] = request.POST.get('repair_cost')

        carRepairObject = CarRepair.objects.create(**updates)

        carloan_repair_start = datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.repair_start, '%Y-%m-%d'), datetime.time(7, 0))
        carloan_repair_end = datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.repair_end, '%Y-%m-%d'), datetime.time(17, 0)) if carRepairObject.repair_end else datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.end_estimate, '%Y-%m-%d'), datetime.time(17, 0)) 

        reservationObject = Reservation.objects.create(
            reservation_datetime_start = carloan_repair_start,
            reservation_datetime_end = carloan_repair_end,
            reserved_car = carObject,
            repair_reservation = True
        )

        carRepairObject.reservation = reservationObject
        carRepairObject.save()

        CarDamageObject.repair_created = True
        CarDamageObject.save()

        return redirect('edit_repair_from_accident', repair_id = carRepairObject.id)

    return render(request, 'create_repair_from_accident.html', context)


def create_repair_general(request):
    
    context = {}

    cars = Car.objects.exclude(car_license_plate=None).order_by('car_license_plate')

    context.update({
        'cars': cars,
    })

    if request.method == "POST":

        updates = {}

        carObject = Car.objects.get(car_license_plate=request.POST.get('car_license_plate'))
        updates['car'] = carObject
        updates['caused_by_wear'] = True
        updates['caused_by_accident'] = False

        if request.POST.get('repair_start'):
            updates['repair_start'] = request.POST.get('repair_start')

        if request.POST.get('cost_estimate'):
            updates['cost_estimate'] = request.POST.get('cost_estimate')

        if request.POST.get('repair_end'):
            updates['repair_end'] = request.POST.get('repair_end')

        if request.POST.get('end_estimate'):
            updates['end_estimate'] = request.POST.get('end_estimate')

        if request.POST.get('repair_cost'):
            updates['repair_cost'] = request.POST.get('repair_cost')

        if request.POST.get('repair_reason'):
            updates['repair_reason'] = request.POST.get('repair_reason')

        carRepairObject = CarRepair.objects.create(**updates)

        carloan_repair_start = datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.repair_start, '%Y-%m-%d'), datetime.time(7, 0))
        carloan_repair_end = datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.repair_end, '%Y-%m-%d'), datetime.time(17, 0)) if carRepairObject.repair_end else datetime.datetime.combine(datetime.datetime.strptime(carRepairObject.end_estimate, '%Y-%m-%d'), datetime.time(17, 0)) 

        reservationObject = Reservation.objects.create(
            reservation_datetime_start = carloan_repair_start,
            reservation_datetime_end = carloan_repair_end,
            reserved_car = carObject,
            repair_reservation = True,
        )

        carRepairObject.reservation = reservationObject
        carRepairObject.save()

        return redirect('edit_repair', repair_id = carRepairObject.id)

    return render(request, 'create_repair_general.html', context)


def show_repairs(request):

    context = {}

    carRepairs = CarRepair.objects.all()
    accidentsWithoutRepairsCreated = CarDamage.objects.filter(repair_created=False)

    context.update({
        'repairs': carRepairs,
        'accidents': accidentsWithoutRepairsCreated
    })

    return render(request, 'show_repairs.html', context)


def edit_repair(request, repair_id):

    context = {}

    repairObject = CarRepair.objects.get(id=repair_id)

    context.update({
        'repair': repairObject,
        'approvers': ['Vajda'],
        'confirmers': ['Vajda'],
        'closers': [''],
    })

    if request.method == "POST":
        
        updates = {
            'repair_reason' : request.POST.get('repair_reason'),
            'repair_start' : request.POST.get('repair_start'),
            'cost_estimate' : request.POST.get('cost_estimate'),
            'end_estimate' : request.POST.get('end_estimate'),
            'confirmed' : request.POST.get('confirmed', False),
            'approved' : request.POST.get('approved', False),
            'closed' : request.POST.get('closed', False),
            'repair_cost' : request.POST.get('repair_cost'),
            'repair_end' : request.POST.get('repair_end'),
            'notes' : request.POST.get('notes'),
            'srm_number': request.POST.get('srm_number'),
        }

        if not updates['confirmed'] == False:
            updates['confirmed'] = True

        if not updates['approved'] == False:
            updates['approved'] = True

        if not updates['closed'] == False:
            updates['closed'] = True


        for key, value in updates.items():
            if value:
                setattr(repairObject, key, value)
        
        repairObject.save()
        message = "Uloženo"

        carloan_repair_start = datetime.datetime.combine(datetime.datetime.strptime(repairObject.repair_start, '%Y-%m-%d'), datetime.time(7, 0))
        carloan_repair_end = datetime.datetime.combine(datetime.datetime.strptime(repairObject.repair_end, '%Y-%m-%d'), datetime.time(17, 0)) if repairObject.repair_end else datetime.datetime.combine(datetime.datetime.strptime(repairObject.end_estimate, '%Y-%m-%d'), datetime.time(17, 0)) 

        reservationObject = repairObject.reservation
        reservationObject.reservation_datetime_start = carloan_repair_start
        reservationObject.reservation_datetime_end = carloan_repair_end
        reservationObject.save()

        context.update({
            'message': message,
        })

    return render(request, 'edit_repair.html', context)


def edit_repair_from_accident(request, repair_id):

    context = {}

    repairObject = CarRepair.objects.get(id=repair_id)
    carloanObject = repairObject.carloan
    accidentObject = CarDamage.objects.get(carloan=carloanObject)

    context.update({
        'repair': repairObject,
        'approvers': ['Vajda'],
        'confirmers': ['Vajda'],
        'closers': [''],
        'accident': accidentObject,
    })

    if request.method == "POST":
        
        updates = {
            'repair_start' : request.POST.get('repair_start'),
            'cost_estimate' : request.POST.get('cost_estimate'),
            'end_estimate' : request.POST.get('end_estimate'),
            'confirmed' : request.POST.get('confirmed', False),
            'approved' : request.POST.get('approved', False),
            'closed' : request.POST.get('closed', False),
            'repair_cost' : request.POST.get('repair_cost'),
            'repair_end' : request.POST.get('repair_end'),
            'notes' : request.POST.get('notes'),
            'srm_number': request.POST.get('srm_number'),
        }

        if not updates['confirmed'] == False:
            updates['confirmed'] = True

        if not updates['approved'] == False:
            updates['approved'] = True

        if not updates['closed'] == False:
            updates['closed'] = True

        
        for key, value in updates.items():
            if key not in ['approved', 'confirmed', 'closed'] and value:
                setattr(repairObject, key, value)
            if key in ['approved', 'confirmed', 'closed']:
                setattr(repairObject, key, value)
        
        repairObject.save()
        message = "Uloženo"

        carloan_repair_start = datetime.datetime.combine(datetime.datetime.strptime(repairObject.repair_start, '%Y-%m-%d'), datetime.time(7, 0))
        carloan_repair_end = datetime.datetime.combine(datetime.datetime.strptime(repairObject.repair_end, '%Y-%m-%d'), datetime.time(17, 0)) if repairObject.repair_end else datetime.datetime.combine(datetime.datetime.strptime(repairObject.end_estimate, '%Y-%m-%d'), datetime.time(17, 0)) 

        reservationObject = repairObject.reservation
        reservationObject.reservation_datetime_start = carloan_repair_start
        reservationObject.reservation_datetime_end = carloan_repair_end
        reservationObject.save()

        repairObject = CarRepair.objects.get(id=repair_id)

        context.update({
            'message': message,
            'repair': repairObject,
        })

    return render(request, 'edit_repair_from_accident.html', context)


def find_carloan_by_qrcode(request):
    print('carloan qr code', request.POST)
    reservation = Reservation.objects.filter(reserved_car__car_license_plate=request.POST.get('data').replace('http://10.49.34.115/carpool/show_car?license_plate=', "").replace("/", ""), reservation_user=request.user, reservation_used=False).order_by('-reservation_datetime_start').first()

    return HttpResponse(reservation.id)


@login_required
@csrf_exempt
def user_admin(request):

    users = CarProfile.objects.exclude(user__email="").order_by('user__last_name')

    context = {
        'carpool_users': users,
    }

    if request.method == "POST":
        request_data = json.loads(request.body)
        if request_data['role'] == 'admin':
            CarProfile.objects.filter(id=request_data['user-id']).update(is_admin=request_data['checked'])
        if request_data['role'] == 'superuser':
            CarProfile.objects.filter(id=request_data['user-id']).update(is_superuser=request_data['checked'])

    return render(request, 'user_admin.html', context)


@csrf_exempt
def delete_car(request):
    car = Car.objects.get(car_license_plate = json.loads(request.body)['license-plate'])
    car.delete()

    return JsonResponse({'status': 'okay'})


@csrf_exempt
def edit_car(request):
    request_data = json.loads(request.body)
    print(request_data)
    car = Car.objects.get(car_license_plate = request_data['license-plate'])
    setattr(car, request_data['field'], request_data['value'])
    car.save()

    return JsonResponse({'status': 'okay'})


@csrf_exempt
def get_car_history(request):
    car = Car.objects.get(car_license_plate = json.loads(request.body)['license-plate'])
    reservations_data = Reservation.objects.filter(reserved_car=car).order_by('reservation_datetime_start')
    carloans_data = CarLoan.objects.filter(reservation__in=reservations_data)

    reservations = {}
    carloans = {}

    for reservation in reservations_data:
        reservations[reservation.id] = {
            'start': reservation.reservation_datetime_start,
            'end': reservation.reservation_datetime_end,
            'user': {
                'last_name': reservation.reservation_user.last_name,
                'first_name': reservation.reservation_user.first_name,
            },
            'used': reservation.reservation_used,
            'created': reservation.created_at,
            'updated': reservation.updated_at,
            'destination': reservation.destination,
            'kilometres': reservation.kilometres,
            'reservation_id': reservation.id,
        }

    for carloan in carloans_data:
        carloans[carloan.id] = {
            'destination': carloan.reservation.destination,
            'user': {
                'last_name': carloan.reservation.reservation_user.last_name,
                'first_name': carloan.reservation.reservation_user.first_name,
            },
            'start': carloan.carloan_start,
            'end': carloan.carloan_end,
            'closed': carloan.closed,
            'carloan_id': carloan.id,
        }

    return JsonResponse({'reservations': reservations, 'carloans': carloans})


def referent(request):

    context = {
        'referents': Referent.objects.all(),
    }

    return render(request, 'referent.html', context)

###################################
# def email_checker():

def galerie_vypujcek(request):
    if request.method == "POST":
        print('how')
    if request.method == "GET":
        return render(request, 'attachment_img_gellery.html', {})




def display_returned_car(request):
    if request.method == "GET":
        print("huh")

        return render(request, 'display_returned_car.html', {})

@csrf_exempt
def display_loaned_car(request):

    if request.method == "POST":
        carId = request.POST.get('carId')

        

        return JsonResponse({'message': ':D'})

    if request.method == "GET":

        fieldsInterior = [
            ('vehicle-cleanness', 'Čistota vozu'),
            ('carpets', 'Stav koberečků'),
            ('seats', 'Stav sedadel'),
            ('trunk', 'Stav zavazadlového prostoru'),
            ('mandatory-equipment', 'Povinná výbava'),
            ('interior-other', 'Ostatní'),
            ('tank-status', 'Stav nádrže'),
            ('tachometer-value', 'Stav tachometru'),
            ('active-warning', 'Kontrolka servisu'),
        ]

        fieldsExterior = [
            ('front-bumper', 'Přední nárazník'),
            ('rear-bumper', 'Zadní nárazník'),
            ('lights', 'Stav světel'),
            ('car-body', 'Stav karoserie'),
            ('tires', 'Stav pneumatik'),
            ('windshield', 'Stav čelního skla'),
            ('washer-fluid', 'Kapalina v ostřikovačích'),
            ('exterior-other', 'Ostatní'),
        ]

        context = {
            'fieldsInterior': fieldsInterior,
            'fieldsExterior': fieldsExterior
        }

        return render(request, 'display_loaned_car.html', context)