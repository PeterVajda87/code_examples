# Generated by Django 3.1.1 on 2023-02-01 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MachiningRecords',
            fields=[
                ('id', models.BigAutoField(db_column='id', primary_key=True, serialize=False)),
                ('duvod', models.TextField(db_column='duvod')),
                ('zacatek_prostoje', models.DateTimeField(db_column='zacatek_prostoje')),
                ('konec_prostoje', models.DateTimeField(db_column='konec_prostoje')),
            ],
        ),
    ]
