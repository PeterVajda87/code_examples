# Generated by Django 3.1.1 on 2022-11-15 08:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0004_auto_20221115_0846'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='kpi',
            name='float_value',
        ),
        migrations.RemoveField(
            model_name='kpi',
            name='shift',
        ),
        migrations.RemoveField(
            model_name='kpi',
            name='text_value',
        ),
    ]
