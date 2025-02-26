# Generated by Django 5.1.4 on 2024-12-24 00:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0002_file_ingestion_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='config_progress',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='file',
            name='status',
            field=models.CharField(choices=[('pending_config', 'In configurazione'), ('pending_upload', 'In caricamento'), ('ready', 'Pronto')], default='pending_config', max_length=20),
        ),
    ]
