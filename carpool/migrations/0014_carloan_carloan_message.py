# Generated by Django 2.1.7 on 2020-09-21 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0013_auto_20200918_2004'),
    ]

    operations = [
        migrations.AddField(
            model_name='carloan',
            name='carloan_message',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
