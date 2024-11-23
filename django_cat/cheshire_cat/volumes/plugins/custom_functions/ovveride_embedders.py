from cat.mad_hatter.decorators import hook
from cat.looking_glass.stray_cat import StrayCat


@hook  # default priority = 1
def agent_fast_reply(fast_reply, cat: StrayCat):
    import json

    try:
        with open("/app/cat/plugins/custom_functions/count_calls.json", 'r+') as file:
            data = json.load(file)
            data["llm_calls"] += 1  # Incrementa il valore di "llm_calls"
            
            # Torna all'inizio del file per sovrascrivere
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()  # Elimina eventuali dati residui
    except Exception as e:
        print(f"Error while updating count_calls.json.json: {e}")

    
    return fast_reply
    

@hook
def before_cat_recalls_memories(cat):
    import json

    try:
        with open("/app/cat/plugins/custom_functions/count_calls.json", 'r+') as file:
            data = json.load(file)
            data["embedder_calls"] += 1  # Incrementa il valore di "llm_calls"
            
            # Torna all'inizio del file per sovrascrivere
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()  # Elimina eventuali dati residui
    except Exception as e:
        print(f"Error while updating count_calls.json.json: {e}")

    
# @hook
# def before_rabbithole_splits_text(docs, cat: StrayCat):
#     for doc in docs:

#         prompt = f"SUMMERIZE THE FOLLOWING TEXT: {doc.page_content}"

        
#         doc.page_content = cat.llm(prompt)
#     return docs


# @hook 
# def before_rabbithole_insert_memory(doc, cat):
#     # insert the user id metadata
#     print(f"\n\n\n{doc.metadata["category"]}\n\n\n")
#     doc.metadata["category"] = "cheshire-cat-docs"

#     return doc