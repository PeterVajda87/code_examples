# Generated by Django 3.0.6 on 2020-06-03 17:43

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0022_auto_20200603_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='managed_ccs',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
