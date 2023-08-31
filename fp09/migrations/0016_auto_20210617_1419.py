# Generated by Django 3.1.2 on 2021-06-17 14:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0015_auto_20210617_1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='downtimefromline',
            name='uid',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 17, 14, 19, 4, 834105)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 17, 14, 19, 4, 834160)),
        ),
    ]
