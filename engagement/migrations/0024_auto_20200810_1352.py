# Generated by Django 2.1.15 on 2020-08-10 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagement', '0023_auto_20200805_1847'),
    ]

    operations = [
        migrations.CreateModel(
            name='RangedAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numeric_low', models.IntegerField()),
                ('string_low', models.CharField(max_length=10)),
                ('numeric_zero', models.IntegerField()),
                ('string_zero', models.CharField(max_length=10)),
                ('numeric_high', models.IntegerField()),
                ('string_high', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='TextAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('length_limit', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='question',
            name='boolean_answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='numeric_answer_high',
        ),
        migrations.RemoveField(
            model_name='question',
            name='numeric_answer_low',
        ),
        migrations.RemoveField(
            model_name='question',
            name='text_answer',
        ),
        migrations.AddField(
            model_name='question',
            name='answer',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='detail_of_answer',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='question',
            name='type_of_answer',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='textanswer',
            name='question',
            field=models.ManyToManyField(blank=True, related_name='text_answer', to='engagement.Question'),
        ),
        migrations.AddField(
            model_name='rangedanswer',
            name='question',
            field=models.ManyToManyField(blank=True, related_name='ranged_answer', to='engagement.Question'),
        ),
    ]
