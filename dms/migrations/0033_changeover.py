# Generated by Django 3.1.1 on 2022-12-06 13:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0032_auto_20221206_1219'),
    ]

    operations = [
        migrations.CreateModel(
            name='Changeover',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changeover_start', models.DateTimeField(null=True)),
                ('changeover_end', models.DateTimeField(null=True)),
                ('line', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.line')),
                ('next_part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='next_part', to='dms.partdata')),
                ('previous_part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='previous_part', to='dms.partdata')),
            ],
        ),
    ]
