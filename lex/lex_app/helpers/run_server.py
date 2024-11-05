import os
import sys
import django
from multiprocessing import Process, Manager
import time
from uvicorn import Config, Server
import asyncio
from lex.lex_app.decorators.LexSingleton import LexSingleton

def make_migrations():
    from django.core.management import call_command

    call_command("makemigrations")
    call_command("migrate")

def django_setup():
    import sys
    import os
    import django

    sys.path.append(os.getenv("LEX_APP_PACKAGE_ROOT"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lex_app.settings")
    os.environ.setdefault("PROJECT_ROOT", os.getenv("PROJECT_ROOT_DIR"))
    os.environ.setdefault("LEX_APP_PACKAGE_ROOT", os.getenv("LEX_APP_PACKAGE_ROOT"))
    os.environ.setdefault("METAGPT_PROJECT_ROOT", os.getenv("METAGPT_PROJECT_ROOT"))
    os.environ["CALLED_FROM_START_COMMAND"] = "False"
    django.setup()

def start_server(shared_state):
    django_setup()
    make_migrations()
    config = Config("lex_app.asgi:application", loop="asyncio", port=8001)
    server = Server(config)

    shared_state['is_running'] = True

    asyncio.run(server.serve())

@LexSingleton
class ServerManager:
    def __init__(self):
        self.manager = Manager()
        self.shared_state = self.manager.dict()
        self.shared_state['is_running'] = False
        self.process = None

    def is_alive(self):
        return self.shared_state.get('is_running', False) and self.process and self.process.is_alive()

    def stop_server(self):
        if self.shared_state.get('is_running', False):
            if self.process:
                self.process.terminate()
                self.process.join()
            self.shared_state['is_running'] = False
        return self

    def restart_server(self):
        self.stop_server()
        self.process = Process(target=start_server, args=(self.shared_state,), daemon=True)
        self.process.start()
        time.sleep(1)  # Wait a moment to ensure the server starts
        return self

def shutdown(server_manager):
    server_manager.stop_server()
