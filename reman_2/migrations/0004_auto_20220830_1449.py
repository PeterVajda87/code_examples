# Generated by Django 3.1.1 on 2022-08-30 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reman_2', '0003_auto_20220830_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='header',
            name='actual_finish_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='header',
            name='release_date',
            field=models.DateField(null=True),
        ),
    ]
