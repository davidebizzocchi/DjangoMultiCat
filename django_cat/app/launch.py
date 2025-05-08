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
        # Dynamically import the specified module
        file_path = settings.BASE_DIR / module_name / "launch.py"

        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        # Create spec from file
        spec = importlib.util.spec_from_file_location("launch", str(file_path))
        module = importlib.util.module_from_spec(spec)
        sys.modules["launch"] = module
        spec.loader.exec_module(module)

        # Check if module has a `main` function
        if hasattr(module, "main"):
            main_function = getattr(module, "main")

            # Start the `main` function in a separate thread
            thread = Thread(target=main_function)
            thread.start()

            ic(f"Launched `main` function from {module_name}.launch in a separate thread.")
        else:
            ic(f"No `main` function found in {module_name}.launch.")
    except ModuleNotFoundError:
        ic(f"Module {file_path} not found.")
    except Exception as e:
        ic(f"Error while launching `main` from {module_name}.launch: {e}")

from app.signals import server_start

def main():
    """
    Iterate through apps specified in `settings.YOUR_APP` and launch their `main` function.
    """
    # for app_label in getattr(settings, "YOUR_APP", []):
        # call_main_in_thread(app_label)

    import app.config
    
    ic(server_start)
    server_start.send(sender=None)
