# Generated by Django 2.1.15 on 2020-08-20 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0059_auto_20200728_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='hours',
            field=models.FloatField(blank=True, default=7.5, null=True),
        ),
    ]
