# Generated by Django 3.0.6 on 2020-07-23 14:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0053_auto_20200723_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offer',
            name='end',
        ),
        migrations.RemoveField(
            model_name='offer',
            name='start',
        ),
    ]
