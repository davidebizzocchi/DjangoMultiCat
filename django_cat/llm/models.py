import uuid
from django.db import models
from common.utils import BaseUserModel
from cheshire_cat.types import LLMRequest
from users.models import UserProfile


class LLM(BaseUserModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    llm_class = models.CharField(max_length=255)
    config = models.JSONField(default=dict)

    def model_kwargs(self):
        return {
            "name": str(self.uuid),
            "llm_class": self.llm_class,
            "config": self.config,
        }

    @property
    def llm(self):
        """
        Returns the LLM instance.
        """
        return LLMRequest.model_validate(self.model_kwargs())

    def model_dump(self):
        """
        Dumps the model to a dictionary.
        """

        return self.llm.model_dump()
    
    def save_llm(self):
        return self.client.update_llm(self.llm)

    def save(self, *args, **kwargs):
        """
        Override save method to ensure the LLM instance is created correctly.
        """
        self.save_llm()
        super().save(*args, **kwargs)

    @staticmethod
    def get_llm_schemas(user: UserProfile):
        """
        Returns the LLM schemas.
        """
        return user.client.get_llm_schemas()
    
    def delete(self, *args, **kwargs):
        """
        Override delete method to ensure the LLM instance is deleted correctly.
        """
        self.client.delete_llm(str(self.uuid))
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"