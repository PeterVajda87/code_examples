# Generated by Django 3.1.1 on 2023-01-11 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obc4', '0004_auto_20221208_1347'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThingworxDowntime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('downtime_beginning', models.DateTimeField(null=True)),
                ('downtime_end', models.DateTimeField(null=True)),
                ('downtime_text_thingworx', models.CharField(blank=True, max_length=1024)),
                ('downtime_category', models.CharField(blank=True, max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='ThingworxStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_text_1', models.CharField(max_length=255)),
                ('status_text_2', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=255)),
            ],
        ),
    ]