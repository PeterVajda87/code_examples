# Generated by Django 3.1.1 on 2022-02-22 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0012_auto_20220221_0811'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='part',
            name='criticality',
        ),
        migrations.RemoveField(
            model_name='part',
            name='recommended_part',
        ),
        migrations.AddField(
            model_name='part',
            name='part_class',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='spareparts',
            name='criticality',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='spareparts',
            name='recommended_part',
            field=models.BooleanField(null=True),
        ),
    ]
