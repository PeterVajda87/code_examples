# Generated by Django 3.1.1 on 2023-01-23 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0052_kpi_api_alias'),
    ]

    operations = [
        migrations.AddField(
            model_name='linekpitarget',
            name='value',
            field=models.FloatField(default=1),
        ),
    ]
