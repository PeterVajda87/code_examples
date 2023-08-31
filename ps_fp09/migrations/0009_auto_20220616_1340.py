# Generated by Django 3.1.1 on 2022-06-16 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ps_fp09', '0008_chart_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChartType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='chart',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ps_fp09.charttype'),
        ),
    ]