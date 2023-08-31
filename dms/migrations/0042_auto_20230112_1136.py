# Generated by Django 3.1.1 on 2023-01-12 11:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dms', '0041_auto_20230111_0622'),
    ]

    operations = [
        migrations.CreateModel(
            name='DMSUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dms_role', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_name', models.CharField(max_length=32)),
                ('shift_duration', models.IntegerField(default=8)),
                ('responsible', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.dmsuser')),
            ],
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color_code', models.CharField(max_length=32)),
            ],
        ),
        migrations.DeleteModel(
            name='DMSRole',
        ),
        migrations.AddField(
            model_name='dmsuser',
            name='shift',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dms.shift'),
        ),
        migrations.AddField(
            model_name='dmsuser',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]