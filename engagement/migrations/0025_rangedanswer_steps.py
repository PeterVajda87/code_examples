# Generated by Django 2.1.15 on 2020-08-10 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0024_auto_20200810_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='rangedanswer',
            name='steps',
            field=models.IntegerField(blank=True, default=3, null=True),
        ),
    ]
