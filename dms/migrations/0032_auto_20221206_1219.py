# Generated by Django 3.1.1 on 2022-12-06 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0031_calculation_with_part'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calculation',
            name='with_part',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]