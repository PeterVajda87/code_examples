# Generated by Django 3.1.1 on 2022-12-05 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0020_calculation'),
    ]

    operations = [
        migrations.AddField(
            model_name='calculation',
            name='connection',
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
