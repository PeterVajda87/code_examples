# Generated by Django 3.1.2 on 2022-06-21 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0059_damagereports'),
    ]

    operations = [
        migrations.AddField(
            model_name='damagereports',
            name='repair_created',
            field=models.BooleanField(default=False),
        ),
    ]
