# Generated by Django 3.0.6 on 2020-06-03 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0020_auto_20200603_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='is_manager',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='worker',
            name='is_supervisor',
            field=models.BooleanField(default=False),
        ),
    ]
