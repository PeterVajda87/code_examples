# Generated by Django 3.1.1 on 2021-06-15 16:20

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0010_auto_20210615_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 15, 16, 20, 0, 288483)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 15, 16, 20, 0, 288524)),
        ),
    ]
