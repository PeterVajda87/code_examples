# Generated by Django 3.0.5 on 2020-04-28 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0005_auto_20200428_0826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='manager',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
