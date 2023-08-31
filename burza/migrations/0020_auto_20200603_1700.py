# Generated by Django 3.0.6 on 2020-06-03 17:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0019_remove_worker_prod_unit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignment',
            old_name='target_prod_unit',
            new_name='target_cost_center',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='target_prod_unit',
            new_name='target_cost_center',
        ),
    ]
