# Generated by Django 3.0.5 on 2020-04-28 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0008_auto_20200428_0859'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='manager',
            field=models.CharField(default='NA', max_length=80),
        ),
    ]
