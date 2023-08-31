from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class CarProfile(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)


class Car(models.Model):
    shell_number = models.CharField(max_length=30, blank=True, null=True, verbose_name="Shell číslo")
    shell_kb_number = models.CharField(max_length=3, blank=True, null=True, verbose_name="Shell KB číslo")
    pin = models.CharField(max_length=4, blank=True, null=True, verbose_name="PIN")
    car_license_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="SPZ")
    technical_certificate = models.CharField(max_length=12, blank=True, null=True, verbose_name="Číslo technického průkazu")
    department = models.CharField(max_length=20, blank=True, null=True, verbose_name="Oddělení")
    contract_number = models.CharField(max_length=8, blank=True, null=True, verbose_name="Čislo smlouvy")
    date_init = models.DateTimeField(blank=True, null=True, verbose_name="Datum pořízení")
    leasing_duration = models.IntegerField(blank=True, null=True, verbose_name="Délka leasingu")
    leasing_end = models.DateTimeField(blank=True, null=True, verbose_name="Konec leasingu")
    monthly_payment = models.FloatField(blank=True, null=True, verbose_name="Měsíční platba")
    kms_limit = models.IntegerField(blank=True, null=True, verbose_name="Km v leasingu")
    car_price = models.FloatField(blank=True, null=True, verbose_name="Cena")
    pool_car = models.BooleanField(default=False, verbose_name="Pool auto")
    manager_car = models.BooleanField(default=False, verbose_name="Manažer auto")
    car_manufacturer = models.CharField(max_length=50, verbose_name="Výrobce")
    car_make = models.CharField(max_length=50, verbose_name="Model")
    car_mileage = models.IntegerField(blank=True, null=True, verbose_name="Stav km")
    car_status = models.CharField(max_length=30, verbose_name="Status")
    car_information = models.JSONField(blank=True, null=True, verbose_name="Informace")
    car_history = models.JSONField(blank=True, null=True, verbose_name="Historie")
    car_owner = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, verbose_name="Oddělení/Manažer")
    fuel_consumption_theoretical = models.FloatField(blank=True, null=True, verbose_name="Spotřeba teoretická")
    fuel_consumption_real = models.FloatField(blank=True, null=True, verbose_name="Spotřeba reální")
    repair_ongoing = models.BooleanField(default=False)
    next_service_date = models.DateField(null=True, blank=True)
    next_service_kms = models.IntegerField(null=True, blank=True)
    technical_control_expiry = models.DateField(null=True, blank=True)
    active_warning = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    def get_fields(self):
        return [(field.verbose_name, field.value_from_object(self)) for field in Car._meta.fields if not field.name in ['id', 'car_information', 'car_history', 'car_owner']]

    def get_header(self):
        return [(field.name) for field in self.__class__._meta.fields]



class Reservation(models.Model):
    reservation_datetime_start = models.DateTimeField()
    reservation_datetime_end = models.DateTimeField()
    reserved_car = models.ForeignKey(to=Car, on_delete=models.SET_NULL, null=True)
    reservation_user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True)
    reservation_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    repair_reservation = models.BooleanField(default=False)
    destination = models.CharField(max_length=250, blank=True, null=True)
    kilometres = models.IntegerField(null=True)
    is_special = models.BooleanField(default=False)

    def get_header(self):
        return [(field.name) for field in self.__class__._meta.fields]


class CarLoan(models.Model):
    reservation = models.ForeignKey(to=Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    carloan_start = models.DateTimeField(blank=True, null=True)
    carloan_end = models.DateTimeField(blank=True, null=True)
    closed = models.BooleanField(default=False)


class CarDamage(models.Model): 
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True)
    traffic_accident = models.BooleanField(default=False, null=True)
    accident_description = models.CharField(max_length=500, blank=True, null=True)
    driver_role = models.TextField(blank=True, null=True)
    accident_date = models.DateField(blank=True, null=True)
    repair_created = models.BooleanField(default=False)


class DamageImage(models.Model):
    image = models.ImageField(upload_to='carpool/pickup_images/')
    pickup_report = models.ForeignKey(to=CarDamage, on_delete=models.CASCADE)
    field = models.CharField(max_length=64)


class PickupReport(models.Model):
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True)
    pickup_person = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    pickup_car = models.ForeignKey(to=Car, on_delete=models.SET_NULL, null=True)
    pickup_datetime = models.DateTimeField()
    vehicle_cleanness = models.BooleanField(default=True)
    carpets = models.BooleanField(default=True)
    seats = models.BooleanField(default=True)
    trunk = models.BooleanField(default=True)
    mandatory_equipment = models.BooleanField(default=True)
    interior_other = models.BooleanField(default=True)
    front_bumper = models.BooleanField(default=True)
    rear_bumper  = models.BooleanField(default=True)
    lights = models.BooleanField(default=True)
    car_body = models.BooleanField(default=True)
    tires  = models.BooleanField(default=True)
    windshield = models.BooleanField(default=True)
    tank_status = models.IntegerField(null=True)
    washer_fluid = models.BooleanField(default=True)
    exterior_other = models.BooleanField(default=True)
    tachometer_value = models.IntegerField(null=True)
    notes = models.CharField(blank=True, max_length=4096)
    active_warning = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def get_header(self):
        return [(field.name) for field in self.__class__._meta.fields]


class PickupImage(models.Model):
    image = models.ImageField(upload_to='carpool/pickup_images/')
    pickup_report = models.ForeignKey(to=PickupReport, on_delete=models.CASCADE)
    field = models.CharField(max_length=64)


class ReturnReport(models.Model):
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True)
    return_datetime = models.DateTimeField()
    notes = models.CharField(max_length=1024, blank=True)
    car_damage = models.CharField(max_length=500)
    tachometer_value = models.IntegerField(null=True)
    tank_status = models.IntegerField(null=True)


class Refueling(models.Model):
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True)
    fuel_bought_amount = models.IntegerField()
    fuel_bought_sum = models.FloatField()
    fuel_bought_date = models.DateField(null=True)


class CarRepair(models.Model):
    car = models.ForeignKey(to=Car, on_delete=models.SET_NULL, null=True, blank=True)
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True, blank=True)
    cost_estimate = models.IntegerField(blank=True, null=True)
    repair_cost = models.IntegerField(blank=True, null=True)
    repair_start = models.DateField(blank=True, null=True)
    repair_end = models.DateField(blank=True, null=True)
    end_estimate = models.DateField(blank=True, null=True)
    caused_by_accident = models.BooleanField(default=False)
    caused_by_wear = models.BooleanField(default=False)
    repair_reason = models.TextField(blank=True, null=True)
    srm_number = models.CharField(max_length=50)
    confirmed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    notes = models.CharField(max_length=3500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    reservation = models.ForeignKey(to=Reservation, on_delete=models.SET_NULL, null=True)

    
class DamageReport(models.Model):
    carloan = models.ForeignKey(to=CarLoan, on_delete=models.SET_NULL, null=True)
    car_mileage = models.IntegerField(blank=True, null=True, verbose_name="Stav km")
    reservation_datetime_start = models.DateTimeField()
    reservation_datetime_end = models.DateTimeField()
    return_datetime = models.DateTimeField()
    part_damaged = models.CharField(max_length=100)
    description = models.CharField(max_length=3500, blank=True, null=True)
    repair_created = models.BooleanField(default=False)


class Referent(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    test_date = models.DateField(null=True)