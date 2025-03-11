from pydantic import Field

from cat.db.models import generate_uuid, generate_timestamp

from cat.plugins.multicat.types import Agent


class AgentDB(Agent):
    updated_at: int = Field(default_factory=generate_timestamp)
