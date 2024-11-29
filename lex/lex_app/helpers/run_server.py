import json
from multiprocessing import Process, Manager, set_start_method
import os
import sys
import django
import time

from django.db import IntegrityError
from uvicorn import Config, Server
import asyncio
from lex.lex_app.decorators.LexSingleton import LexSingleton


def make_migrations(project_name):
    from django.core.management import call_command
    try:
        call_command("migrate", project_name, "zero", "--no-input")
        call_command("makemigrations", project_name)
        call_command("migrate", project_name, "--no-input")
        return True, None
    except (Exception, KeyError, ImportError, RuntimeError, IntegrityError, ValueError, TypeError) as e:
        print(f"Migration error: {str(e)}")
        return False, str(e)



def django_setup():
    sys.path.append(os.getenv("LEX_APP_PACKAGE_ROOT"))
    # Ensure environment variables are set before django setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lex_app.settings")
    os.environ.setdefault("PROJECT_ROOT", os.getenv("PROJECT_ROOT_DIR"))
    os.environ.setdefault("LEX_APP_PACKAGE_ROOT", os.getenv("LEX_APP_PACKAGE_ROOT"))
    os.environ.setdefault("METAGPT_PROJECT_ROOT", os.getenv("METAGPT_PROJECT_ROOT"))
    os.environ["CALLED_FROM_START_COMMAND"] = "False"

    try:
        django.setup()
        return True, None
    except Exception as e:
        print(f"Django setup error: {str(e)}")
        return False, str(e)


def start_server(shared_state):
    # Set spawn method for Linux compatibility
    if sys.platform.startswith('linux'):
        set_start_method('spawn', force=True)
    success_1, result = django_setup()

    response_data = {
        'success': success_1,
        'test_results': {
            'failures': result,
            'error': "",
            'traceback': ""
        },
        'console_output': {
            'stdout': [],
            'stderr': [result]
        }
    }

    if not success_1:
        shared_state['exit'] = json.dumps(response_data)
        time.sleep(2)
    success_2, result = make_migrations(project_name=shared_state['project_name'])

    response_data = {
        'success': success_2,
        'test_results': {
            'failures': result,
            'error': "",
            'traceback': ""
        },
        'console_output': {
            'stdout': [],
            'stderr': [result]
        }
    }

    if not success_2:
        shared_state['exit'] = json.dumps(response_data)


    config = Config("lex_app.asgi:application", loop="asyncio", port=8001)
    server = Server(config)
    shared_state['is_running'] = True
    asyncio.run(server.serve())


@LexSingleton
class ServerManager:
    def __init__(self, project_name):
        # Set spawn method at class initialization
        if sys.platform.startswith('linux'):
            set_start_method('spawn', force=True)
        self.project_name = project_name
        self._init()

    def _init(self):
        self.manager = Manager()
        self.shared_state = self.manager.dict()
        self.shared_state['is_running'] = False
        self.shared_state['exit'] = None
        self.shared_state['project_name'] = self.project_name

        self.process = None

    def is_migration_setup_error(self):
        return self.shared_state.get("exit") != None
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
        self._init()
        # Ensure environment is set up before creating new process
        # django_setup()
        self.process = Process(target=start_server, args=(self.shared_state,), daemon=True)
        self.process.start()
        time.sleep(2)  # Increased wait time for Linux
        return self


def shutdown(server_manager):
    server_manager.stop_server()