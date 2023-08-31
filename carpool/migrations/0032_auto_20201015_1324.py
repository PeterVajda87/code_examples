# Generated by Django 3.1.1 on 2020-10-15 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0031_carrepair_pending_closure'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='carrepair',
            name='repair_costs',
        ),
        migrations.AddField(
            model_name='carrepair',
            name='cost_estimate',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='carrepair',
            name='end_estimate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='carrepair',
            name='repair_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='carrepair',
            name='repair_end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='carrepair',
            name='repair_start',
            field=models.DateField(blank=True, null=True),
        ),
    ]
