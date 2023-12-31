# Generated by Django 4.0.6 on 2022-07-20 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ThingworxLocalsmartkpi',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('creationtime', models.CharField(blank=True, max_length=100, null=True)),
                ('machine', models.CharField(blank=True, max_length=100, null=True)),
                ('productiontime', models.CharField(blank=True, max_length=100, null=True)),
                ('ispartok', models.IntegerField(blank=True, null=True)),
                ('partnumber', models.CharField(blank=True, max_length=100, null=True)),
                ('serialnumber', models.CharField(blank=True, max_length=100, null=True)),
                ('confirmtosap', models.IntegerField(blank=True, null=True)),
                ('confirmedtosap', models.IntegerField(blank=True, null=True)),
                ('sapconfirmationresult', models.CharField(blank=True, max_length=100, null=True)),
                ('sapoperationnumber', models.CharField(blank=True, max_length=100, null=True)),
                ('ordernumber', models.CharField(blank=True, max_length=100, null=True)),
                ('timeperpartsec', models.CharField(blank=True, max_length=100, null=True)),
                ('scrapreason', models.CharField(blank=True, max_length=100, null=True)),
                ('isupdated', models.IntegerField(blank=True, null=True)),
                ('numberofparts', models.IntegerField(blank=True, null=True)),
                ('station', models.CharField(blank=True, max_length=100, null=True)),
                ('json', models.CharField(blank=True, max_length=100, null=True)),
                ('utccreationtime', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
