# Generated by Django 3.0.6 on 2020-08-17 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0035_auto_20200817_1327'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='description',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]
