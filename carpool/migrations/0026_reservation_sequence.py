# Generated by Django 3.1.1 on 2020-10-14 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0025_accidentreport_driver_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='sequence',
            field=models.IntegerField(default=1),
        ),
    ]
