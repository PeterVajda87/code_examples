# Generated by Django 3.1.1 on 2022-11-15 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0005_auto_20221115_0848'),
    ]

    operations = [
        migrations.AddField(
            model_name='deviation',
            name='shift',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='deviation',
            name='description',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
