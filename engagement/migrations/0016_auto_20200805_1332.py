# Generated by Django 3.0.6 on 2020-08-05 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0015_auto_20200805_1327'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='section',
        ),
        migrations.AddField(
            model_name='question',
            name='section',
            field=models.ManyToManyField(blank=True, null=True, related_name='question', to='engagement.Section'),
        ),
        migrations.RemoveField(
            model_name='section',
            name='section_questionnaire',
        ),
        migrations.AddField(
            model_name='section',
            name='section_questionnaire',
            field=models.ManyToManyField(blank=True, null=True, to='engagement.QuestionnaireTemplate'),
        ),
    ]
