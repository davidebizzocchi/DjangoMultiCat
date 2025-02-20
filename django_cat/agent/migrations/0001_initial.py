# Generated by Django 5.1.5 on 2025-02-19 23:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user', '-updated_at'),
            },
        ),
    ]
