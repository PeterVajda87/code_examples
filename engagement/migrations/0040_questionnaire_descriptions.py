# Generated by Django 2.1.15 on 2020-08-21 15:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0039_auto_20200820_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='descriptions',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]
