# Generated by Django 3.0.6 on 2020-06-04 12:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0025_remove_worker_managed_ccs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='not_available',
        ),
    ]
