# Generated by Django 3.0.6 on 2020-07-08 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('burza', '0035_assignment_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=10)),
                ('priority', models.IntegerField(blank=True, null=True)),
                ('text', models.CharField(max_length=200)),
                ('scale_low', models.IntegerField(blank=True, null=True)),
                ('scale_high', models.IntegerField(blank=True, null=True)),
                ('answer', models.IntegerField(blank=True, null=True)),
                ('questionnaire', models.ManyToManyField(to='engagement.Questionnaire')),
            ],
        ),
        migrations.CreateModel(
            name='AnsweredQuestionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost_center', models.CharField(max_length=10)),
                ('note', models.CharField(max_length=100)),
                ('answerer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answerer', to='burza.Worker')),
                ('questioner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questioner', to='burza.Worker')),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagement.Questionnaire')),
            ],
        ),
    ]
