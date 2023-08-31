# Generated by Django 3.1.1 on 2022-08-30 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Losses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(max_length=12)),
            ],
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material_number', models.CharField(max_length=32)),
                ('material_name', models.CharField(max_length=128)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reman_2.customer')),
            ],
        ),
        migrations.CreateModel(
            name='MaterialGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material_group', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(max_length=12)),
                ('activity', models.CharField(max_length=12)),
                ('work_center', models.CharField(max_length=12)),
                ('operation_text', models.CharField(max_length=255)),
                ('operation_quantity', models.FloatField()),
                ('confirmed_yield', models.FloatField()),
                ('scrap', models.FloatField()),
                ('rework_quantity', models.FloatField()),
                ('material_number', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reman_2.material')),
            ],
        ),
        migrations.AddField(
            model_name='material',
            name='material_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reman_2.materialgroup'),
        ),
        migrations.CreateModel(
            name='Header',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(max_length=12, unique=True)),
                ('order_type', models.CharField(max_length=4)),
                ('start_date', models.DateField()),
                ('finish_date', models.DateField()),
                ('order_quantity', models.FloatField()),
                ('quantity_delivered', models.FloatField()),
                ('rework_quantity', models.FloatField()),
                ('confirmed_scrap', models.FloatField()),
                ('system_status', models.CharField(max_length=128)),
                ('release_date', models.DateField()),
                ('actual_finish_date', models.DateField()),
                ('material_number', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reman_2.material')),
            ],
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.CharField(max_length=12)),
                ('requirement_quantity', models.FloatField()),
                ('quantity_withdrawn', models.FloatField()),
                ('material', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='material', to='reman_2.material')),
                ('pegged_requirement', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pegged_requirement', to='reman_2.material')),
            ],
        ),
    ]