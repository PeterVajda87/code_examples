# Generated by Django 3.1.2 on 2022-05-30 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0048_auto_20201026_1518'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pickupreport',
            name='car_damage',
        ),
        migrations.RemoveField(
            model_name='pickupreport',
            name='car_exterior_cleannes',
        ),
        migrations.RemoveField(
            model_name='pickupreport',
            name='car_fuel',
        ),
        migrations.RemoveField(
            model_name='pickupreport',
            name='car_interior_cleannes',
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='car_body',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='carpets',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='exterior_other',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='front_bumper',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='interior_other',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='lights',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='mandatory_equipment',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='rear_bumper',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='seats',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='tank',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='tires',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='trunk',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='vehicle_cleanness',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='washer_fluid',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pickupreport',
            name='windshield',
            field=models.BooleanField(default=True),
        ),
    ]
