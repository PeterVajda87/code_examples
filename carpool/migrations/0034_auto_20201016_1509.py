# Generated by Django 3.1.1 on 2020-10-16 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0033_carrepair_repair_reason'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accidentreport',
            old_name='closed',
            new_name='repair_created',
        ),
    ]