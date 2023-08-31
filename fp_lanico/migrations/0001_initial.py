# Generated by Django 3.1.1 on 2022-12-13 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LanicoMontaz',
            fields=[
                ('Record', models.IntegerField(db_column='Record', primary_key=True, serialize=False)),
                ('Zakazka', models.CharField(blank=True, db_column='Zakazka', max_length=15, null=True)),
                ('Typ_fp', models.CharField(blank=True, db_column='Typ_FP', max_length=20, null=True)),
                ('Cas', models.DateTimeField(db_column='Cas')),
                ('Datum', models.DateTimeField(db_column='Datum')),
                ('Plneni', models.CharField(blank=True, db_column='Plneni', max_length=30, null=True)),
                ('Montaz_st1', models.CharField(blank=True, db_column='Montaz_ST1', max_length=30, null=True)),
                ('Montaz_st2', models.CharField(blank=True, db_column='Montaz_ST2', max_length=30, null=True)),
                ('Montaz_st3', models.CharField(blank=True, db_column='Montaz_ST3', max_length=30, null=True)),
                ('Interval', models.FloatField(blank=True, db_column='Interval', null=True)),
                ('Identifikace', models.CharField(blank=True, db_column='Identifikace', max_length=20, null=True)),
                ('Rework', models.IntegerField(blank=True, db_column='Rework', null=True)),
            ],
            options={
                'db_table': 'Lanico_montaz',
                'managed': False,
            },
        ),
    ]