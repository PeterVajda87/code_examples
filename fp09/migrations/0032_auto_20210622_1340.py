# Generated by Django 3.1.2 on 2021-06-22 13:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0031_auto_20210622_1339'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 13, 40, 25, 647121)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 13, 40, 25, 647157)),
        ),
    ]
