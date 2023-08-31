from django.db import models


class MachiningRecords(models.Model):
    id = models.BigAutoField(db_column='id', primary_key=True)  
    duvod = models.TextField(db_column='duvod') 
    prostoj = models.TextField(db_column='prostoj') 
    stroj = models.TextField(db_column='stroj') 
    zacatek_prostoje = models.DateTimeField(db_column='zacatek_prostoje')
    konec_prostoje = models.DateTimeField(db_column='konec_prostoje')
    

##### PETER SI UDELAL CVICENI PROTOZE POTREBOVAL AKUTNE PAR ZMEN #####
class DowntimeCategory(models.Model):
    category = models.CharField(max_length=64)
    

class Downtime(models.Model):
    category = models.ForeignKey(to=DowntimeCategory, on_delete=models.SET_NULL, null=True)
    downtime = models.CharField(max_length=255)


class Machine(models.Model):
    machine = models.CharField(max_length=32)
    
    
class RecordedDowntime(models.Model):
    downtime = models.ForeignKey(to=Downtime, on_delete=models.SET_NULL, null=True)
    machine = models.ForeignKey(to=Machine, on_delete=models.SET_NULL, null=True)
    downtime_beginning = models.DateTimeField()
    downtime_end = models.DateTimeField()
    comment = models.CharField(max_length=1024, blank=True, null=True)
    
    