# Generated by Django 3.1.1 on 2022-03-22 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0021_auto_20220321_1421'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailnotification',
            name='notify_local_only',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(blank=True, default='Logistics', max_length=255, null=True),
        ),
    ]
