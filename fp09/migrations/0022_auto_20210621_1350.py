# Generated by Django 3.1.2 on 2021-06-21 13:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0021_auto_20210621_1327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 21, 13, 50, 3, 99019)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 21, 13, 50, 3, 99045)),
        ),
    ]
