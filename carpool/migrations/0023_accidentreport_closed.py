# Generated by Django 3.1.1 on 2020-10-12 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0022_auto_20201012_1448'),
    ]

    operations = [
        migrations.AddField(
            model_name='accidentreport',
            name='closed',
            field=models.BooleanField(default=False),
        ),
    ]