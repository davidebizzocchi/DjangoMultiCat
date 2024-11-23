from pathlib import Path
import sys
from django.conf import settings
from threading import Thread
import importlib
import logging
from icecream import ic
import importlib.util

# logger = logging.getLogger(__name__)

def call_main_in_thread(module_name):
    """
    Import the `main` function from the given module name and run it in a separate thread.
    """
    try:
        # Importa dinamicamente il modulo specificato
        file_path = settings.BASE_DIR / module_name / "launch.py"

        if not file_path.exists():
            raise FileNotFoundError(f"Il file {file_path} non esiste.")

        # Crea uno spec dal file
        spec = importlib.util.spec_from_file_location("launch", str(file_path))
        module = importlib.util.module_from_spec(spec)
        sys.modules["launch"] = module
        spec.loader.exec_module(module)

        # module = importlib.import_module(f"code.{module_name}.launch")

        # Verifica se il modulo ha una funzione `main`
        if hasattr(module, "main"):
            main_function = getattr(module, "main")

            # Avvia la funzione `main` in un thread separato
            thread = Thread(target=main_function)
            thread.start()

            ic(f"Launched `main` function from {module_name}.launch in a separate thread.")
        else:
            ic(f"No `main` function found in {module_name}.launch.")
    except ModuleNotFoundError:
        ic(f"Module {file_path} not found.")
    except Exception as e:
        ic(f"Error while launching `main` from {module_name}.launch: {e}")

def main():
    """
    Itera attraverso le app specificate in `settings.YOUR_APP` e lancia la funzione `main`.
    """
    for app_label in getattr(settings, "YOUR_APP", []):
        call_main_in_thread(app_label)
