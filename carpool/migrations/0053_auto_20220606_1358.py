# Generated by Django 3.1.1 on 2022-06-06 13:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0052_pickupreport_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarDamage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('traffic_accident', models.BooleanField(default=False, null=True)),
                ('accident_description', models.CharField(blank=True, max_length=500, null=True)),
                ('driver_role', models.TextField(blank=True, null=True)),
                ('accident_date', models.DateField(blank=True, null=True)),
                ('repair_created', models.BooleanField(default=False)),
                ('carloan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='carpool.carloan')),
            ],
        ),
        migrations.CreateModel(
            name='DamageImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='carpool/pickup_images/')),
                ('field', models.CharField(max_length=64)),
                ('pickup_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='carpool.cardamage')),
            ],
        ),
        migrations.AddField(
            model_name='refueling',
            name='fuel_bought_date',
            field=models.DateField(null=True),
        ),
        migrations.DeleteModel(
            name='AccidentReport',
        ),
    ]
