# Generated by Django 3.1.2 on 2022-02-28 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0015_auto_20220228_1218'),
    ]

    operations = [
        migrations.CreateModel(
            name='Columns',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label_cz', models.CharField(max_length=255, null=True)),
                ('label_en', models.CharField(max_length=255, null=True)),
                ('technical_name', models.CharField(max_length=255, null=True)),
                ('part_related', models.BooleanField()),
                ('line_related', models.BooleanField()),
                ('crucial', models.BooleanField()),
            ],
        ),
    ]
