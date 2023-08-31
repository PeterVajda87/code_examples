# Generated by Django 3.1.1 on 2022-09-29 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reman_2', '0008_material_is_root_material'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rootmaterialcomposition',
            name='is_manually_added',
        ),
        migrations.RemoveField(
            model_name='rootmaterialcomposition',
            name='is_manually_removed',
        ),
        migrations.AddField(
            model_name='rootmaterialcomposition',
            name='refreshed',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
