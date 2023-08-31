# Generated by Django 3.1.1 on 2021-09-03 09:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0050_question_helper'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaire',
            name='interviewee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interviewee', to='engagement.employee'),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='interviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interviewer', to='engagement.employee'),
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='questionnaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='engagement.questionnairetemplate'),
        ),
    ]