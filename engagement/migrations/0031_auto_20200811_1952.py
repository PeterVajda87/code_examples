# Generated by Django 2.1.15 on 2020-08-11 19:52

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0030_auto_20200811_1930'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='questionnaire',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='filled_in',
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='answers',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]
