# Generated by Django 3.0.6 on 2020-08-25 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0040_questionnaire_descriptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]