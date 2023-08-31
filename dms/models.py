from django.db import models
from django.contrib.auth.models import User


class Shift(models.Model):
    color_code = models.CharField(max_length=32)
    
    
class DMSUser(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    dms_role = models.CharField(max_length=32)
    shift = models.ForeignKey(to=Shift, on_delete=models.SET_NULL, null=True)
    
    
class Area(models.Model):
    area_name = models.CharField(max_length=32)
    
    
class Line(models.Model):
    line_name = models.CharField(max_length=32)
    shift_duration = models.IntegerField(default=8)
    area = models.ForeignKey(to=Area, on_delete=models.SET_NULL, null=True)
    thingworx_name = models.CharField(max_length=128)
    
    def __str__(self):
        return self.line_name
    

class ShiftLeader(models.Model):
    shift_leader = models.ForeignKey(to=DMSUser, on_delete=models.SET_NULL, null=True)
    area = models.ForeignKey(to=Area, on_delete=models.SET_NULL, null=True)
    
    
class KPI(models.Model):
    kpi_name = models.CharField(max_length=64)
    api_alias = models.CharField(max_length=64, default="")
    
    def __str__(self):
        return self.kpi_name
    
    
class LineKPItarget(models.Model):
    line = models.ForeignKey(to=Line, on_delete=models.CASCADE)
    kpi = models.ForeignKey(to=KPI, on_delete=models.CASCADE)
    value = models.FloatField(default=1)
    
    
class OperatorsAttendance(models.Model):
    line = models.ForeignKey(to=Line, on_delete=models.SET_NULL, null=True)
    interval_start = models.DateTimeField()
    interval_end = models.DateTimeField(null=True)
    worker_id = models.IntegerField()
    worker_type = models.IntegerField() ## 8 or 12
    

class OperatorsAbsence(models.Model):
    area = models.ForeignKey(to=Area, on_delete=models.SET_NULL, null=True)
    absence_category = models.CharField(max_length=32, null=True)
    interval_start = models.DateTimeField()
    interval_end = models.DateTimeField(null=True)
    worker_id = models.IntegerField()
    worker_type = models.IntegerField() ## 8 or 12
    

class ShiftChange(models.Model):
    shift_beginning = models.DateTimeField()
    shift_end = models.DateTimeField()
    shift_line = models.ForeignKey(to=Line, on_delete=models.SET_NULL, null=True)
    five_s_done = models.BooleanField(default=False)
    handover_confirmed = models.BooleanField(default=False)
    text_info_1 = models.CharField(max_length=2048, blank=True, null=True)
    text_info_2 = models.CharField(max_length=2048, blank=True, null=True)


class Deviation(models.Model):
    deviation_id = models.BigIntegerField()
    details = models.JSONField()