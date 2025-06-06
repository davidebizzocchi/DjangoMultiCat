# Generated by Django 5.1.7 on 2025-03-24 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_id', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('name', models.CharField(default='', max_length=255)),
                ('instructions', models.TextField(default='')),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('user', '-updated_at'),
            },
        ),
    ]
