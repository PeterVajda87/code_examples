# Generated by Django 3.1.1 on 2020-10-16 15:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('carpool', '0034_auto_20201016_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='carloan',
            name='repair_loan',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='carloan',
            name='car_loaner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='carloan',
            name='reservation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='carpool.reservation'),
        ),
    ]
