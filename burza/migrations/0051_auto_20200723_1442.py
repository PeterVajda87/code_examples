# Generated by Django 3.0.6 on 2020-07-23 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0050_auto_20200723_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='offer',
            name='start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
