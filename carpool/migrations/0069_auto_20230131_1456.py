# Generated by Django 3.1.1 on 2023-01-31 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0068_returnreport_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_special',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='returnreport',
            name='tank_status',
            field=models.IntegerField(null=True),
        ),
    ]
