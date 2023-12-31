# Generated by Django 3.1.1 on 2022-03-07 14:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0010_auto_20220307_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downtime',
            name='train_circuit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.traincircuit'),
        ),
        migrations.AlterField(
            model_name='traincircuit',
            name='number',
            field=models.IntegerField(),
        ),
    ]
