# Generated by Django 3.1.2 on 2021-06-22 12:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0025_auto_20210622_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 12, 39, 42, 35398)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 12, 39, 42, 35431)),
        ),
    ]
