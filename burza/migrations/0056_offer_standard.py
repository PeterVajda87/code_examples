# Generated by Django 3.0.6 on 2020-07-23 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0055_auto_20200723_1447'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='standard',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]