# handlers/handle_events.py
import os
import importlib

def load_events(bot):
    events_dir = os.path.join(os.path.dirname(__file__), "../events")
    for root, _, files in os.walk(events_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                rel_path = os.path.relpath(os.path.join(root, file), events_dir)
                module_path = "events." + rel_path.replace(os.sep, ".")[:-3]
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, "setup"):
                        module.setup(bot)  # ← Not awaited
                        print(f"[+] Loaded event: {module_path}")
                except Exception as e:
                    print(f"[!] Failed to load {module_path}: {e}")
