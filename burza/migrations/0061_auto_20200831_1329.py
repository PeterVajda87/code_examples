# Generated by Django 2.1.15 on 2020-08-31 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0060_assignment_hours'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='hours',
            field=models.FloatField(blank=True, default=8, null=True),
        ),
    ]
