# Generated by Django 3.0.6 on 2020-08-05 13:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0014_auto_20200805_1321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='questionnaire',
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_name', models.CharField(max_length=40)),
                ('section_description', models.CharField(max_length=200)),
                ('section_questionnaire', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagement.QuestionnaireTemplate')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question', to='engagement.Section'),
        ),
    ]
