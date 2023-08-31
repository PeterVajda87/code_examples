# Generated by Django 3.0.6 on 2020-08-05 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0013_auto_20200805_1216'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=30)),
                ('author', models.CharField(blank=True, max_length=50, null=True)),
                ('date_created', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='question',
            name='numeric_answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='scale_high',
        ),
        migrations.RemoveField(
            model_name='question',
            name='scale_low',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='author',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='name',
        ),
        migrations.AddField(
            model_name='question',
            name='numeric_answer_high',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='numeric_answer_low',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='weight',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='questionnaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagement.QuestionnaireTemplate'),
        ),
        migrations.AlterField(
            model_name='question',
            name='questionnaire',
            field=models.ManyToManyField(blank=True, related_name='question', to='engagement.QuestionnaireTemplate'),
        ),
    ]
