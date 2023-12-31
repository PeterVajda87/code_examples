# Generated by Django 3.1.1 on 2021-06-15 12:41

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Downtime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DowntimeFromLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beginning', models.DateTimeField(default=datetime.datetime(2021, 6, 15, 12, 41, 29, 471676))),
                ('end', models.DateTimeField(default=datetime.datetime(2021, 6, 15, 12, 41, 29, 471702))),
                ('comment', models.CharField(blank=True, max_length=512, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fp09.category')),
                ('downtime', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fp09.downtime')),
                ('station', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fp09.station')),
            ],
        ),
        migrations.AddField(
            model_name='downtime',
            name='station',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fp09.station'),
        ),
    ]
