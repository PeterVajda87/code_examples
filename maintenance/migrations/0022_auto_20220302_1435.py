# Generated by Django 3.1.1 on 2022-03-02 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0021_auto_20220302_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='delivery_time',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
    ]
