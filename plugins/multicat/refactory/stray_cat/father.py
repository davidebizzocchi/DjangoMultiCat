from typing import Dict, List
from cat.auth.permissions import AuthUserInfo

from cat.convo.messages import UserMessage
from cat.log import log

from cat.looking_glass.cheshire_cat import CheshireCat

from cat.looking_glass.stray_cat import StrayCat

from cat.plugins.multicat.decorators import option

# Common
from cat.plugins.multicat.refactory.stray_cat.common import CommonStrayCat
from cat.plugins.multicat.refactory.stray_cat.son import SonStrayCat


# Adapt the StrayCat to curate the SonStrayCat (the perfect father)
@option(StrayCat)
class FatherStrayCat(StrayCat, CommonStrayCat):
    bevoled_son_chat_id = "default"

    def __init__(
        self,
        user_data: AuthUserInfo
    ):
        log.warning("FatherStrayCat created")
        
        # user data
        self.__user_id = user_data.name # TODOV2: use id
        self.__user_data = user_data

        self.stray_sons: Dict[str, SonStrayCat] = {}

        super().__init__(user_data)

    def create_son(self, chat_id: str):
        """Create a new son"""

        self.stray_sons[chat_id] = SonStrayCat(
            chat_id,
            self,
            self.user_data,
        )
        
        return self.stray_sons[chat_id]
    
    def load_working_memory_from_cache(self):
        """Load the working memory of bevoled son from the cache"""
        return self.get_beloved_son().load_working_memory_from_cache()
    
    def update_working_memory_cache(self):
        """Update the working memory of bevoled son in the cache"""
        return self.get_beloved_son().update_working_memory_cache()
    
    @property
    def chat_id(self):
        """Return the chat id of the beloved son"""
        return self.bevoled_son_chat_id

    @property
    def working_memory(self):
        """Return the working memory of the beloved son"""
        return self.get_beloved_son().working_memory
    
    @working_memory.setter
    def working_memory(self, value):
        """Set the working memory of the beloved son"""
        self.get_beloved_son().working_memory = value

    @property
    def chat_list(self) -> List:
        """Return the list of chat ids"""
        return list(self.stray_sons.keys())
    
    def create_bevoled_son(self):
        """Create the beloved son"""
        return self.create_son(self.bevoled_son_chat_id)
    
    def get_son(self, chat_id: str):
        """Get the son"""
        if chat_id not in self.stray_sons:
            return self.create_son(chat_id)
        
        return self.stray_sons[chat_id]
    
    def get_beloved_son(self):
        """Get the beloved son"""
        return self.get_son(self.bevoled_son_chat_id)

    # @property
    # def working_memory(self) -> WorkingMemory:
    #     """Return the beloved son"""
    #     return self.get_beloved_son().working_memory

    def __build_why(self):
        return self.get_beloved_son().__build_why()
    
    def __call__(self, message_dict):        
        message_dict["user_id"] = self.user_id

        user_message = UserMessage.model_validate(message_dict)
        chat_id = user_message.chat_id

        # now recall son
        return self.get_son(chat_id)(message_dict)
    
    def __repr__(self):
        return f"FatherStrayCat(user_id={self.user_id})"
    
    def __str__(self) -> str:
        return f"FatherStrayCat of {self.user_id}"
    
    @property
    def user_id(self) -> str:
        """The user's id.
        
        Returns
        -------
        user_id : str
            Current user's id.
        """
        return self.__user_id
    
    @property
    def user_data(self) -> AuthUserInfo:
        """`AuthUserInfo` object containing user data.

        Returns
        -------
        user_data : AuthUserInfo
            Current user's data.
        """
        return self.__user_data
    
    @property
    def _llm(self):
        """Instance of langchain `LLM`.
        Only use it if you directly want to deal with langchain, prefer method `cat.llm(prompt)` otherwise.
        """
        return CheshireCat()._llm

    @property
    def embedder(self):
        """Langchain `Embeddings` object.

        Returns
        -------
        embedder : langchain `Embeddings`
            Langchain embedder to turn text into a vector.


        Examples
        --------
        >>> cat.embedder.embed_query("Oh dear!")
        [0.2, 0.02, 0.4, ...]
        """
        return CheshireCat().embedder

    @property
    def memory(self):
        """Gives access to the long term memory, containing vector DB collections (episodic, declarative, procedural).

        Returns
        -------
        memory : LongTermMemory
            Long term memory of the Cat.


        Examples
        --------
        >>> cat.memory.vectors.episodic
        VectorMemoryCollection object for the episodic memory.
        """
        return CheshireCat().memory

    @property
    def rabbit_hole(self):
        """Gives access to the `RabbitHole`, to upload documents and URLs into the vector DB.

        Returns
        -------
        rabbit_hole : RabbitHole
            Module to ingest documents and URLs for RAG.


        Examples
        --------
        >>> cat.rabbit_hole.ingest_file(...)
        """
        return CheshireCat().rabbit_hole

    @property
    def mad_hatter(self):
        """Gives access to the `MadHatter` plugin manager.

        Returns
        -------
        mad_hatter : MadHatter
            Module to manage plugins.


        Examples
        --------

        Obtain the path in which your plugin is located
        >>> cat.mad_hatter.get_plugin().path
        /app/cat/plugins/my_plugin

        Obtain plugin settings
        >>> cat.mad_hatter.get_plugin().load_settings()
        {"num_cats": 44, "rows": 6, "remainder": 0}
        """
        return CheshireCat().mad_hatter

    @property
    def main_agent(self):
        """Gives access to the default main agent.
        """
        return CheshireCat().main_agent

    @property
    def white_rabbit(self):
        """Gives access to `WhiteRabbit`, to schedule repeatable tasks.

        Returns
        -------
        white_rabbit : WhiteRabbit
            Module to manage cron tasks via `APScheduler`.

        Examples
        --------
        Send a websocket message after 30 seconds
        >>> def ring_alarm_api():
        ...     cat.send_chat_message("It's late!")
        ...
        ... cat.white_rabbit.schedule_job(ring_alarm_api, seconds=30)
        """
        return CheshireCat().white_rabbit
    
    @property
    def cache(self):
        """Gives access to internal cache."""
        return CheshireCat().cache
