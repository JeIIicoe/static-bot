import os
import importlib

async def load_commands(bot):
    commands_dir = os.path.join(os.path.dirname(__file__), "../commands")
    for root, _, files in os.walk(commands_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                rel_path = os.path.relpath(os.path.join(root, file), commands_dir)
                module_path = "commands." + rel_path.replace(os.sep, ".")[:-3]
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, "setup"):
                        await module.setup(bot)
                        print(f"[+] Loaded command: {module_path}")
                except Exception as e:
                    print(f"[!] Failed to load {module_path}: {e}")
