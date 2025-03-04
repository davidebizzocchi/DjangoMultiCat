from django.dispatch import receiver
from agent.utils import sync_agent_with_cat
from app.signals import server_start


# receivers
@receiver(server_start)
def create_agents_on_server_start(sender, **kwargs):
    sync_agent_with_cat()