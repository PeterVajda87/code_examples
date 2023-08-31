# Generated by Django 3.1.1 on 2022-12-08 13:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('obc4', '0002_availabilityhelper_shift_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Downtime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('station', models.CharField(blank=True, max_length=255, null=True)),
                ('category', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceBookAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(blank=True, max_length=32)),
                ('status', models.CharField(blank=True, max_length=32)),
                ('title', models.CharField(blank=True, max_length=128)),
                ('description', models.CharField(blank=True, max_length=512)),
                ('responsible', models.CharField(blank=True, max_length=128)),
                ('priority', models.CharField(blank=True, max_length=16)),
                ('planned_finish', models.DateField(null=True)),
                ('finish', models.DateField(null=True)),
                ('created_by', models.CharField(blank=True, max_length=128)),
                ('updated_by', models.CharField(blank=True, max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('ordering', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceBookActionEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=1024)),
                ('owner', models.CharField(blank=True, max_length=1024, null=True)),
                ('planned_end', models.DateField(null=True)),
                ('service_book_action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='obc4.servicebookaction')),
            ],
        ),
        migrations.AddField(
            model_name='servicebookaction',
            name='station',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='obc4.station'),
        ),
        migrations.CreateModel(
            name='AddressedDowntime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('downtime', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='obc4.downtime')),
                ('service_book_action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='obc4.servicebookaction')),
            ],
        ),
    ]