# Generated by Django 2.1.15 on 2020-08-05 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0016_auto_20200805_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='section',
            field=models.ManyToManyField(blank=True, related_name='question', to='engagement.Section'),
        ),
        migrations.AlterField(
            model_name='questionnairetemplate',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='author', to='engagement.SurveyProfile'),
        ),
        migrations.AlterField(
            model_name='section',
            name='section_questionnaire',
            field=models.ManyToManyField(blank=True, to='engagement.QuestionnaireTemplate'),
        ),
    ]