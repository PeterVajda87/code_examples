# Generated by Django 3.1.1 on 2022-07-11 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0064_auto_20220629_1244'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='kms_status_current_year',
        ),
        migrations.RemoveField(
            model_name='carloan',
            name='car_loaner',
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='active_warning',
            field=models.BooleanField(default=False),
        ),
    ]
