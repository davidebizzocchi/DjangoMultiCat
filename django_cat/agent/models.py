from threading import Thread
from django.db import models
from cheshire_cat.types import AgentRequest, Agent as AgentModel
from app.utils import BaseUserModel

class Agent(BaseUserModel):
    agent_id = models.CharField(max_length=255, null=True, blank=True, default=None)
    name = models.CharField(max_length=255, default="")
    instructions = models.TextField(default="")
    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user", "-updated_at")

    def model_dump(self) -> AgentRequest:
        return AgentRequest(
            name=self.name,
            instructions=self.instructions,
            metadata=self.metadata
        ).model_dump()
    
    def full_model_dump(self) -> AgentModel:
        return AgentModel(
            id=self.agent_id,
            name=self.name,
            instructions=self.instructions,
            metadata=self.metadata
        ).model_dump()
    
    @staticmethod
    def get_default(user=None):
        return Agent.objects.get_or_create(agent_id="default", user=user)[0]
    
    @property
    def is_default(self):
        return self.agent_id == "default"
    
    def create_agent(self, save=True):
        agent = self.client.create_agent(self)
        self.agent_id = agent.id

        if save:
            self.save()

        return agent

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.agent_id is None:
            self.create_agent(save=False)
        elif self.pk:
            self.client.update_agent(self)

    def delete(self, *args, **kwargs):
        self.client.delete_agent(self.agent_id)
        
        return super().delete(*args, **kwargs)