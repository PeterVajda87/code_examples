# Generated by Django 3.0.6 on 2020-07-08 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0005_auto_20200708_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='questionnaire',
            field=models.ManyToManyField(blank=True, null=True, related_name='test', to='engagement.Questionnaire'),
        ),
    ]
