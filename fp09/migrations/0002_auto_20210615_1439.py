# Generated by Django 3.1.2 on 2021-06-15 14:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtimefromline',
            name='beginning',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 15, 14, 39, 33, 890439)),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='end',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 15, 14, 39, 33, 890475)),
        ),
    ]
