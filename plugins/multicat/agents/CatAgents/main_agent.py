from cat.agents.main_agent import MainAgent

from cat.plugins.multicat.mad_hatter.limited import MadHatterLimited
from cat.mad_hatter.mad_hatter import MadHatter

from cat.plugins.multicat.settings import MultiCatSettings

class MainAgentLimited(MainAgent):
    def __init__(self, plugins=[]):
        super().__init__()

        self.mad_hatter = MadHatterLimited(plugins=plugins)

    @staticmethod
    def get_for_agent(agent) -> "MainAgentLimited":
        """Get the main agent for the given agent."""
        from cat.log import log

        # Get all plugins in the database
        all_plugins = MadHatter().load_active_plugins_from_db()

        if agent.id == "default":
            base_plugins = all_plugins
        else:
            base_plugins = set(all_plugins) - set(MultiCatSettings.model_validate(MadHatter().get_plugin().load_settings()).limited_plugins)
            base_plugins = list(base_plugins)

            base_plugins.extend(agent.metadata.get("plugins", []))

        return MainAgentLimited(plugins=list(base_plugins))