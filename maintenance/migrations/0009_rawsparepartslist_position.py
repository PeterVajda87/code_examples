# Generated by Django 3.1.1 on 2022-02-09 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0008_auto_20220209_1307'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawsparepartslist',
            name='position',
            field=models.IntegerField(null=True),
        ),
    ]
