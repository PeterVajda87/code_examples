# Generated by Django 3.1.1 on 2022-03-09 12:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0012_profile_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='downtime',
            name='sequence_number',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='specific_numer',
        ),
    ]