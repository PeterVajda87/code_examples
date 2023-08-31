# Generated by Django 3.1.1 on 2022-06-16 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ps_fp09', '0002_station_codename'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now=True)),
                ('quantity', models.IntegerField()),
                ('size', models.CharField(max_length=1)),
            ],
        ),
    ]