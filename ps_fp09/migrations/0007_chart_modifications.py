# Generated by Django 3.1.1 on 2022-06-16 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ps_fp09', '0006_chart_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='chart',
            name='modifications',
            field=models.JSONField(null=True),
        ),
    ]