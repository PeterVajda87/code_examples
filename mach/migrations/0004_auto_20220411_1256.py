# Generated by Django 3.1.2 on 2022-04-11 12:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mach', '0003_auto_20220411_1249'),
    ]

    operations = [
        migrations.RenameField(
            model_name='downtime',
            old_name='name',
            new_name='downtime',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='station',
        ),
        migrations.RemoveField(
            model_name='downtimefromline',
            name='category',
        ),
        migrations.RemoveField(
            model_name='downtimefromline',
            name='uid',
        ),
        migrations.RemoveField(
            model_name='downtimefromline',
            name='uploaded_to_xlsx',
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='downtime',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mach.downtime'),
        ),
        migrations.AlterField(
            model_name='downtimefromline',
            name='station',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mach.station'),
        ),
    ]