# Generated by Django 3.1.2 on 2021-06-22 13:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0028_auto_20210622_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 13, 36, 42, 214266)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end_t',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 22, 13, 36, 42, 214286)),
        ),
    ]