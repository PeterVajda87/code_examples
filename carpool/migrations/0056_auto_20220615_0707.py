# Generated by Django 3.1.1 on 2022-06-15 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0055_auto_20220610_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='car',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
