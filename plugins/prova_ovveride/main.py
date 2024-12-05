from cat.mad_hatter.decorators import option
from cat.rabbit_hole import RabbitHole
from cat.log import log


@option("rabbit_home")
class RabbitHoleCustom(RabbitHole):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.warning("\n\n\nMERDA HA FUNZIONATO!!!!!!\n\n\n")
        