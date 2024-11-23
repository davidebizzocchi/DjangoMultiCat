from cat.mad_hatter.decorators import hook
from cat.looking_glass.stray_cat import StrayCat
from pathlib import Path
import requests
import zipfile
import io
import threading
import time
import json
import xml.etree.ElementTree as ET

plugin_dir = Path("/app/cat/plugins/download_cat_docs")

def download_async(cat: StrayCat):
    # Download
    hidden_dir = plugin_dir / ".hidden/"
    if not hidden_dir.exists():
        hidden_dir.mkdir(parents=True, exist_ok=True)

        repo_url = "https://github.com/cheshire-cat-ai/docs/archive/refs/heads/main.zip"
        response = requests.get(repo_url)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(hidden_dir)

    # Inspect
    cat.send_notification("Cheshire doc downloaded successfully.")

    # json_path = plugin_dir / "Recalled_Memories.json"

    # with open(json_path, "r") as f:
    #     memory = json.load(f)

    # memory = memory["collections"]["declarative"]
    
    xml_path = plugin_dir / "sitemap.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()

        # Definisci il namespace
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Trova tutti gli elementi <loc> e estrai gli URL
    # for url in root.findall('ns:url/ns:loc', namespace):
    #     md_file_path = url.text

    #     cat.rabbit_hole.ingest_file(cat, md_file_path)

    for md_file in hidden_dir.rglob("*.md"):
        md_file_path = str(md_file)

        # find = False
        # for mem in memory:
        #     mem_path = mem["metadata"]["source"]

        #     if md_file_path == mem_path:
        #         find = True
        #         continue

        # if find:
        #     cat.send_chat_message(md_file_path)
        #     continue

        cat.rabbit_hole.ingest_file(cat, md_file_path)

        # time.sleep(15)  # 30hz
    
    cat.send_notification("all file have been successfully ingested.")
    cat.send_chat_message("Avanti, mettimi alla prova")

@hook(priority=2)
def agent_fast_reply(fast_reply, cat: StrayCat):

    last_mex = cat.working_memory.user_message_json["text"]

    # print("\n\n\n")
    # print(os.listdir())
    # print("\n\n\n")

    # TODO: Inserire un tool
    if last_mex == "download_cat_docs":
        cat.send_notification("Download of docs has been started.")
        cat.send_notification("The action may require some minutes.")
        threading.Thread(target=download_async, args=(cat,)).start()
        return {
            "output": "Aspetta..."
        }
    
    return fast_reply