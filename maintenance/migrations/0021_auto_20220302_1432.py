# Generated by Django 3.1.1 on 2022-03-02 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0020_columns_is_boolean'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='delivery_time',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]