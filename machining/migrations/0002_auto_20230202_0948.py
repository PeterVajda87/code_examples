# Generated by Django 3.1.1 on 2023-02-02 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('machining', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='machiningrecords',
            name='prostoj',
            field=models.TextField(db_column='prostoj', default='ADB'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='machiningrecords',
            name='stroj',
            field=models.TextField(db_column='stroj', default='AOH'),
            preserve_default=False,
        ),
    ]
