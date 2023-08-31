# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class LanicoMontaz(models.Model):
    Record = models.IntegerField(db_column='Record', primary_key=True)  # Field name made lowercase.
    Zakazka = models.CharField(db_column='Zakazka', max_length=15, blank=True, null=True)  # Field name made lowercase.
    Typ_fp = models.CharField(db_column='Typ_FP', max_length=20, blank=True, null=True)  # Field name made lowercase.
    Cas = models.DateTimeField(db_column='Cas')  # Field name made lowercase.
    Datum = models.DateTimeField(db_column='Datum')  # Field name made lowercase.
    Plneni = models.CharField(db_column='Plneni', max_length=30, blank=True, null=True)  # Field name made lowercase.
    Montaz_st1 = models.CharField(db_column='Montaz_ST1', max_length=30, blank=True, null=True)  # Field name made lowercase.
    Montaz_st2 = models.CharField(db_column='Montaz_ST2', max_length=30, blank=True, null=True)  # Field name made lowercase.
    Montaz_st3 = models.CharField(db_column='Montaz_ST3', max_length=30, blank=True, null=True)  # Field name made lowercase.
    Interval = models.FloatField(db_column='Interval', blank=True, null=True)  # Field name made lowercase.
    Identifikace = models.CharField(db_column='Identifikace', max_length=20, blank=True, null=True)  # Field name made lowercase.
    Rework = models.IntegerField(db_column='Rework', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Lanico_montaz'
