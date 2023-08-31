# Generated by Django 2.1.7 on 2020-09-04 17:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0063_auto_20200904_1747'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='offer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.Offer'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.Request'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='target_costcenter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.CostCenter'),
        ),
        migrations.AlterField(
            model_name='pendingrequest',
            name='assignment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='burza.Assignment'),
        ),
        migrations.AlterField(
            model_name='pendingrequest',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]