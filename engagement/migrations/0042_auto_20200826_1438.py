# Generated by Django 2.1.15 on 2020-08-26 14:38

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0041_questionnaire_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]