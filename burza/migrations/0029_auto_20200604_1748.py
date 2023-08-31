# Generated by Django 3.0.6 on 2020-06-04 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0028_auto_20200604_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='is_manager',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='worker',
            name='is_supervisor',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='worker',
            name='is_teamleader',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
