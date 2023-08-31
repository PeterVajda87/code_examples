# Generated by Django 3.1.2 on 2020-10-26 15:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('burza', '0066_worker_left'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accidents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nearmiss',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reporter_role', models.CharField(max_length=50)),
                ('datetime_of_nearmiss', models.DateTimeField()),
                ('area', models.CharField(max_length=20)),
                ('place', models.CharField(max_length=50)),
                ('image_urls', models.JSONField(default=dict)),
                ('activity_nearmiss', models.CharField(max_length=500)),
                ('nearmiss_description', models.CharField(max_length=500)),
                ('nearmiss_launcher', models.CharField(max_length=500)),
                ('nearmiss_rootcause', models.CharField(max_length=500)),
                ('immediate_corrective_measures', models.CharField(max_length=500)),
                ('longterm_corrective_measures', models.CharField(max_length=500)),
                ('measures_implementation_date', models.DateField()),
                ('status', models.IntegerField(blank=True, null=True)),
                ('measure_effectiveness', models.CharField(max_length=500)),
                ('fmea_relevant', models.BooleanField()),
                ('sos_revision', models.DateField()),
                ('fmea_implementation', models.DateField()),
                ('reporter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.worker')),
                ('responsible', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Accident',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dob', models.DateField()),
                ('injured_role', models.CharField(max_length=50)),
                ('bozp_aware', models.BooleanField(default=True)),
                ('on_workplace_since', models.DateField()),
                ('injury_classification', models.CharField(max_length=20)),
                ('count_of_injured', models.IntegerField()),
                ('injured_bodypart', models.CharField(max_length=100)),
                ('injury_type', models.CharField(max_length=100)),
                ('accident_datetime', models.DateTimeField()),
                ('hours_worked_before_accident', models.FloatField()),
                ('area', models.CharField(max_length=20)),
                ('place', models.CharField(max_length=50)),
                ('image_urls', models.JSONField(default=dict)),
                ('activity_injury', models.CharField(max_length=500)),
                ('injury_description', models.CharField(max_length=500)),
                ('injury_launcher', models.CharField(max_length=500)),
                ('injury_rootcause', models.CharField(max_length=500)),
                ('injury_rootcause_type', models.CharField(max_length=50)),
                ('immediate_corrective_measures', models.CharField(max_length=500)),
                ('longterm_corrective_measures', models.CharField(max_length=500)),
                ('measures_implementation_date', models.DateField()),
                ('status', models.IntegerField(blank=True, null=True)),
                ('measure_effectiveness', models.CharField(max_length=500)),
                ('alcohol_test', models.BooleanField(default=False)),
                ('protocol_datetime', models.DateTimeField()),
                ('protocol_author_role', models.CharField(max_length=50)),
                ('fmea_relevant', models.BooleanField()),
                ('sos_revision', models.DateField()),
                ('fmea_implementation', models.DateField()),
                ('injured', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.worker')),
                ('protocol_author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='procotol_author', to=settings.AUTH_USER_MODEL)),
                ('responsible', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('witnesses', models.ManyToManyField(related_name='witnesses', to='burza.Worker')),
            ],
        ),
    ]