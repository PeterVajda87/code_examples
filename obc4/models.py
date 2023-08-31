from django.db import models


class AvailabilityHelper(models.Model):
    shift = models.CharField(max_length=1)
    shift_date = models.DateField()
    shift_order = models.IntegerField(null=True)
    available_minutes = models.IntegerField(default=480)


class Station(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    ordering = models.IntegerField(null=True)


class Downtime(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    station = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)


class ServiceBookAction(models.Model):
    station = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=32, blank=True)
    title = models.CharField(max_length=128, blank=True)
    description = models.CharField(max_length=512, blank=True)
    responsible = models.CharField(max_length=128, blank=True)
    priority = models.CharField(max_length=16, blank=True)
    planned_finish = models.DateField(null=True)
    finish = models.DateField(null=True)
    created_by = models.CharField(max_length=128, blank=True)
    updated_by = models.CharField(max_length=128, blank=True)


class ServiceBookActionEntry(models.Model):
    service_book_action = models.ForeignKey(to=ServiceBookAction, on_delete=models.CASCADE)
    description = models.CharField(max_length=1024, blank=True)
    owner = models.CharField(max_length=1024, blank=True, null=True)
    planned_end = models.DateField(null=True)


class AddressedDowntime(models.Model):
    service_book_action = models.ForeignKey(to=ServiceBookAction, on_delete=models.CASCADE)
    downtime = models.ForeignKey(to=Downtime, on_delete=models.SET_NULL, null=True)
    
    
class ThingworxDowntime(models.Model):
    downtime_beginning = models.DateTimeField(null=True)
    downtime_end = models.DateTimeField(null=True)
    downtime_text_thingworx = models.CharField(max_length=1024, blank=True)
    downtime_category = models.CharField(max_length=128, blank=True)
    
    
class ThingworxStatus(models.Model):
    status_text_1 = models.CharField(max_length=255)
    status_text_2 = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=255)