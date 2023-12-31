# Generated by Django 2.1.7 on 2020-09-17 15:13

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0009_auto_20200908_1410'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='car_reserved',
        ),
        migrations.AlterField(
            model_name='car',
            name='car_history',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Historie'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_information',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Informace'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_make',
            field=models.CharField(max_length=50, verbose_name='Model'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_manufacturer',
            field=models.CharField(max_length=50, verbose_name='Výrobce'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_mileage',
            field=models.IntegerField(blank=True, null=True, verbose_name='Stav km'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Oddělení/Manažer'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Cena'),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_status',
            field=models.CharField(max_length=30, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='car',
            name='contract_number',
            field=models.CharField(blank=True, max_length=8, null=True, verbose_name='Čislo smlouvy'),
        ),
        migrations.AlterField(
            model_name='car',
            name='date_init',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Datum pořízení'),
        ),
        migrations.AlterField(
            model_name='car',
            name='department',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Oddělení'),
        ),
        migrations.AlterField(
            model_name='car',
            name='fuel_consumption_real',
            field=models.FloatField(blank=True, null=True, verbose_name='Spotřeba'),
        ),
        migrations.AlterField(
            model_name='car',
            name='fuel_consumption_theoretical',
            field=models.FloatField(blank=True, null=True, verbose_name='Spotřeba teoretická'),
        ),
        migrations.AlterField(
            model_name='car',
            name='kms_yearly',
            field=models.IntegerField(blank=True, null=True, verbose_name='Km ročně'),
        ),
        migrations.AlterField(
            model_name='car',
            name='leasing_duration',
            field=models.IntegerField(blank=True, null=True, verbose_name='Délka leasingu'),
        ),
        migrations.AlterField(
            model_name='car',
            name='leasing_end',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Konec leasingu'),
        ),
        migrations.AlterField(
            model_name='car',
            name='manager_car',
            field=models.BooleanField(default=False, verbose_name='Manažer auto'),
        ),
        migrations.AlterField(
            model_name='car',
            name='monthly_payment',
            field=models.FloatField(blank=True, null=True, verbose_name='Měsíční platba'),
        ),
        migrations.AlterField(
            model_name='car',
            name='pool_car',
            field=models.BooleanField(default=False, verbose_name='Pool auto'),
        ),
    ]
