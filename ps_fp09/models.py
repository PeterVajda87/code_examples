from django.db import models
from django.contrib.auth.models import User


class Station(models.Model):
    name = models.CharField(max_length=64)
    codename = models.CharField(max_length=64)


class Dashboard(models.Model):
    name = models.CharField(max_length=64)
    author = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)


class ChartType(models.Model):
    type = models.CharField(max_length=32, unique=True)
    icon_path = models.CharField(max_length=32, blank=True)

class Chart(models.Model):
    dashboard = models.ManyToManyField(to=Dashboard)
    type = models.ForeignKey(to=ChartType, on_delete=models.SET_NULL, null=True, default=1)
    order = models.IntegerField(null=True)
    name = models.CharField(max_length=64)
    author = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    query = models.CharField(max_length=1000)
    modifications = models.JSONField(null=True)


