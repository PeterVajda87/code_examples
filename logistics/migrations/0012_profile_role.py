# Generated by Django 3.1.1 on 2022-03-09 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0011_auto_20220307_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
