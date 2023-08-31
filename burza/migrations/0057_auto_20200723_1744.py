# Generated by Django 3.0.6 on 2020-07-23 17:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0056_offer_standard'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='end',
            field=models.DateTimeField(blank=True, default=datetime.date(2020, 7, 23)),
        ),
        migrations.AddField(
            model_name='request',
            name='standard',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='request',
            name='start',
            field=models.DateTimeField(blank=True, default=datetime.date(2020, 7, 23)),
        ),
    ]
