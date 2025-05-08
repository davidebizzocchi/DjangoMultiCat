from cat.mad_hatter.decorators import hook
from langchain.docstore.document import Document

from cat.looking_glass.cheshire_cat import CheshireCat
from cat.looking_glass import prompts

from cat.plugins.multicat.types import Agent
from cat.plugins.multicat.refactory.stray_cat.son import SonStrayCat


@hook()
def before_cat_stores_episodic_memory(doc: Document, cat):
    doc.metadata["chat_id"] = cat.chat_id

    return doc

@hook()
def before_cat_recalls_episodic_memories(episodic_recall_config: dict, cat) -> dict:
    if not episodic_recall_config.get("metadata"):
        episodic_recall_config["metadata"] = {}

    episodic_recall_config["metadata"]["chat_id"] = cat.chat_id

    return episodic_recall_config

@hook()
def before_rabbithole_insert_memory(doc: Document, cat):
    doc.metadata["user_id"] = cat.user_id

    return doc

@hook()
def before_cat_recalls_declarative_memories(declarative_recall_config: dict, cat) -> dict:
    if not declarative_recall_config.get("metadata"):
        declarative_recall_config["metadata"] = {}

    metadata = declarative_recall_config["metadata"]

    metadata["user_id"] = cat.user_id

    if "chats_id" not in metadata and cat.chat_id != "default":
        metadata["chats_id"] = [cat.chat_id]

    return declarative_recall_config

@hook()
def after_cat_bootstrap(cat: CheshireCat):
    cat.agents = {}  # [str, Agent] Agent in multicat.types

    cat.agents["default"] = Agent(
        id="default",
        _class=type(cat.main_agent),
        name="Main Agent",
        instructions=prompts.MAIN_PROMPT_PREFIX,
        metadata={}
    )

@hook(priority=0)
def agent_prompt_prefix(prefix, cat):
    if isinstance(cat, SonStrayCat):
        new_instructions = cat.get_instructions()
        if new_instructions:
            prefix = (
                f"{prefix}"
                f"\nYOUR NEW INSTRUCTIONS:\n{new_instructions}\n\n"
            )
    
    return prefix

@hook(priority=0)
def get_memory_type_keys(default_memory_types: list, cat: SonStrayCat) -> list:    
    if cat.is_default_agent():
        return default_memory_types

    if not cat.agent.enable_vector_search:
        default_memory_types.remove("declarative")

        setattr(
            cat.working_memory,
            "declarative_memories",
            list()
        )

    return default_memory_types