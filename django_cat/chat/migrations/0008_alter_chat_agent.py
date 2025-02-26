# Generated by Django 5.1.5 on 2025-02-20 23:44

import agent.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0001_initial'),
        ('chat', '0007_chat_agent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='agent',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=models.SET(agent.models.Agent.get_default), related_name='chats', to='agent.agent'),
        ),
    ]
