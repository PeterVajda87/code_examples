# Generated by Django 3.1.1 on 2022-07-12 12:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0066_auto_20220712_1249'),
    ]

    operations = [
        migrations.CreateModel(
            name='DamageReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('car_mileage', models.IntegerField(blank=True, null=True, verbose_name='Stav km')),
                ('reservation_datetime_start', models.DateTimeField()),
                ('reservation_datetime_end', models.DateTimeField()),
                ('return_datetime', models.DateTimeField()),
                ('part_damaged', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=3500, null=True)),
                ('repair_created', models.BooleanField(default=False)),
                ('carloan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='carpool.carloan')),
            ],
        ),
        migrations.DeleteModel(
            name='DamageReports',
        ),
    ]
