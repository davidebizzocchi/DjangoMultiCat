from cat.mad_hatter.mad_hatter import MadHatter

from cat.plugins.multicat.decorators import get_true_class


class MadHatterLimited(get_true_class(MadHatter)):
    def __init__(self, plugins=[]):
        self.mad_hatter = MadHatter()

        super().__init__()

        self.active_plugins = plugins

        self.find_plugins()

    def find_plugins(self):

        if len(self.active_plugins) == 0:
            return

        self.plugins = {}

        for plugin_name in self.active_plugins:
            try:
                self.plugins[plugin_name] = self.mad_hatter.plugins[plugin_name]

            except KeyError:
                continue

        self.sync_hooks_tools_and_forms()
