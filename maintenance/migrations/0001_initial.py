# Generated by Django 3.1.2 on 2022-02-04 11:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_description', models.CharField(max_length=255, null=True)),
                ('label_1', models.CharField(max_length=255)),
                ('label_2', models.CharField(max_length=255, unique=True)),
                ('manufacturing_number', models.CharField(max_length=255)),
                ('sap_number', models.CharField(max_length=255)),
                ('recommended_part', models.BooleanField(null=True)),
                ('produced_part', models.BooleanField(null=True)),
                ('electrical', models.BooleanField()),
                ('mechanical', models.BooleanField()),
                ('price', models.FloatField()),
                ('delivery_time', models.IntegerField()),
                ('criticality', models.CharField(max_length=16, null=True)),
                ('wearable', models.BooleanField(null=True)),
                ('manufacturer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='maintenance.manufacturer', to_field='name')),
            ],
        ),
        migrations.CreateModel(
            name='SpareParts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('documentation_label', models.CharField(max_length=255, null=True)),
                ('safety_stock', models.CharField(max_length=16, null=True)),
                ('line', models.ManyToManyField(to='maintenance.Line')),
                ('part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='maintenance.part', to_field='label_2')),
            ],
        ),
    ]