# Generated by Django 3.0.5 on 2020-04-27 09:07

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='assignments',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
