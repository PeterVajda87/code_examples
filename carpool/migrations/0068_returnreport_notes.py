# Generated by Django 3.1.1 on 2022-08-25 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0067_auto_20220712_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnreport',
            name='notes',
            field=models.CharField(blank=True, max_length=1024),
        ),
    ]
