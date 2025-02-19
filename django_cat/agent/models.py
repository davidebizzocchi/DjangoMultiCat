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

    def model_dump(self) -> AgentModel:
        if self.agent_id is None:
            return AgentRequest(
                name=self.name,
                instructions=self.instructions,
                metadata=self.metadata
            )
        
        return AgentModel(
            id=self.agent_id,
            name=self.name,
            instructions=self.instructions,
            metadata=self.metadata
        )
    
    def create_agent(self):
        pass

    @property
    def is_default(self):
        return self.agent_id == "default"

    @staticmethod
    def get_default(user=None):
        return Agent.objects.get_or_create(agent_id="default", user=user)[0]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.agent_id is None:
            Thread(target=self.create_agent).start()