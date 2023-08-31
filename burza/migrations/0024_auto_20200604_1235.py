# Generated by Django 3.0.6 on 2020-06-04 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('burza', '0023_worker_managed_ccs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='supervisor',
        ),
        migrations.CreateModel(
            name='Bindings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='burza.Worker')),
                ('supervisor_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor_1', to='burza.Worker')),
                ('supervisor_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor_2', to='burza.Worker')),
                ('supervisor_3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor_3', to='burza.Worker')),
                ('teamleader_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teamleader_1', to='burza.Worker')),
                ('teamleader_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teamleader_2', to='burza.Worker')),
                ('teamleader_3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teamleader_3', to='burza.Worker')),
            ],
        ),
    ]