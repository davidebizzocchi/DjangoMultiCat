from users.models import UserProfile
from agent.models import Agent
from icecream import ic


def sync_agent_with_cat():
    if UserProfile.objects.count() == 0:
        return
    
    first_agent = Agent.get_default()  # select a casual agent
    
    count = first_agent.client.sync_agents()

    ic(f"Created {count} agents on server start")