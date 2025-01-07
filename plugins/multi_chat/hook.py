from cat.mad_hatter.decorators import hook
from langchain.docstore.document import Document

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
