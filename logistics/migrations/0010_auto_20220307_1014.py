# Generated by Django 3.1.1 on 2022-03-07 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0009_auto_20220304_0828'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subcategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subcategory', models.CharField(max_length=255)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.category')),
            ],
        ),
        migrations.CreateModel(
            name='TrainDriver',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('train_driver', models.CharField(max_length=255)),
            ],
        ),
        migrations.DeleteModel(
            name='Columns',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='category',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='logistics_category',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='logistics_downtime',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='logistics_note',
        ),
        migrations.RemoveField(
            model_name='downtime',
            name='production_note',
        ),
        migrations.AddField(
            model_name='downtime',
            name='note_by_logistics',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='downtime',
            name='note_by_production',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='traincircuit',
            name='line',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.line'),
        ),
        migrations.AlterField(
            model_name='downtime',
            name='downtime',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='productionarea',
            name='responsible',
            field=models.ManyToManyField(related_name='production_area_responsible', to='logistics.Profile'),
        ),
        migrations.AddField(
            model_name='downtime',
            name='category_by_logistics',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_by_logistics', to='logistics.category'),
        ),
        migrations.AddField(
            model_name='downtime',
            name='category_by_production',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_by_production', to='logistics.category'),
        ),
        migrations.AddField(
            model_name='downtime',
            name='subcategory_by_logistics',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategory_by_logistics', to='logistics.subcategory'),
        ),
        migrations.AddField(
            model_name='downtime',
            name='subcategory_by_production',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategory_by_production', to='logistics.subcategory'),
        ),
        migrations.AlterField(
            model_name='downtime',
            name='train_driver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.traindriver'),
        ),
    ]
