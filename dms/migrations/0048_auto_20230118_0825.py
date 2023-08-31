# Generated by Django 3.1.1 on 2023-01-18 08:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0047_auto_20230112_1530'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='line',
            name='responsible',
        ),
        migrations.CreateModel(
            name='ShiftLeader',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.line')),
                ('shift_leader', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.dmsuser')),
            ],
        ),
    ]