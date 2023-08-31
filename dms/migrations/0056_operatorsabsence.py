# Generated by Django 3.1.1 on 2023-02-02 12:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0055_auto_20230130_1023'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperatorsAbsence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interval_start', models.DateTimeField()),
                ('interval_end', models.DateTimeField(null=True)),
                ('worker_id', models.IntegerField()),
                ('worker_type', models.IntegerField()),
                ('line', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.line')),
            ],
        ),
    ]
