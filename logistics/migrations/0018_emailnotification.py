# Generated by Django 3.1.1 on 2022-03-15 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0017_auto_20220315_1352'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(blank=True, max_length=255)),
                ('notify_on_create', models.BooleanField(default=True)),
                ('notify_on_update', models.BooleanField(default=False)),
            ],
        ),
    ]
