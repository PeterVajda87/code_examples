# Generated by Django 3.1.1 on 2022-03-11 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0014_auto_20220309_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtime',
            name='downtime_rootcause',
            field=models.CharField(max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='downtime',
            name='status',
            field=models.FloatField(null=True),
        ),
    ]
