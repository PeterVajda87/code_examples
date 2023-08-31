# Generated by Django 3.1.1 on 2022-08-15 12:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fp09', '0052_servicebookaction_servicebookactionentry'),
    ]

    operations = [
        migrations.RenameField(
            model_name='servicebookaction',
            old_name='finished_at',
            new_name='finish',
        ),
        migrations.RenameField(
            model_name='servicebookaction',
            old_name='planned_end',
            new_name='planned_finish',
        ),
        migrations.RemoveField(
            model_name='servicebookaction',
            name='one_time_activity',
        ),
        migrations.CreateModel(
            name='AddressedDowntime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('downtime', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fp09.downtime')),
                ('service_book_action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fp09.servicebookaction')),
            ],
        ),
    ]
