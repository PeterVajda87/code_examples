# Generated by Django 3.1.1 on 2022-06-17 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0057_car_tachometer_value'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='tachometer_value',
        ),
    ]
