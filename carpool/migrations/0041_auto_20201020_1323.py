# Generated by Django 3.1.1 on 2020-10-20 13:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0040_auto_20201020_1316'),
    ]

    operations = [
        migrations.RenameField(
            model_name='carprofile',
            old_name='can_approve_accident',
            new_name='approver',
        ),
        migrations.RenameField(
            model_name='carprofile',
            old_name='can_close_accident',
            new_name='closer',
        ),
        migrations.RenameField(
            model_name='carprofile',
            old_name='can_confirm_accident',
            new_name='confirmer',
        ),
    ]
