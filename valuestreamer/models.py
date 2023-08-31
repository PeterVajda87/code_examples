from django.db import models


class Team(models.Model):
    team_name = models.CharField(max_length=32)
    team_uuid = models.CharField(max_length=128)
    
class KPIentry(models.Model):
    kpi_name = models.CharField(max_length=32)
    kpi_uuid = models.CharField(max_length=128)
    kpi_value_uuid_actual = models.CharField(max_length=128)
    kpi_value_uuid_target = models.CharField(max_length=128)
    team = models.ForeignKey(to=Team, on_delete=models.SET_NULL, null=True)