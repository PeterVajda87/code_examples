# Generated by Django 3.1.1 on 2022-12-06 12:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0035_linebreak'),
    ]

    operations = [
        # migrations.RemoveField(
        #     model_name='linebreak',
        #     name='line',
        # ),
        migrations.AddField(
            model_name='linebreak',
            name='line_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='dms.line'),
        )
    ]
