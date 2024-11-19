import asyncio
import os
import ast
import sys
import time
import networkx as nx

import django
from asgiref.sync import sync_to_async
from django.core.management import call_command
from requests import RequestException

from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex_ai.helpers.post_request import post_request
from lex_ai.metagpt.ProjectGenerator import ProjectGenerator
from lex_ai.metagpt.actions.GenerateJson import GenerateJson
from lex.lex_ai.rag.rag import RAG
from lex.lex_app.helpers.run_server import ServerManager
from metagpt.schema import Message
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts

from metagpt.roles.role import Role
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex.lex_ai.metagpt.generate_test_for_code import generate_test_for_code, generate_test_for_json
from lex.lex_ai.metagpt.run_tests import run_tests, get_failed_test_classes
from lex_ai.metagpt.generate_test_jsons import generate_test_python_jsons, generate_test_python_jsons_alg
from lex_ai.metagpt.roles.LexRole import LexRole
from lex_app.helpers.RequestHandler import RequestHandler
from pprint import pprint




class JsonGenerator(LexRole):
    name: str = "JsonGenerator"
    profile: str = "Expert in generating test jsons"

    def __init__(self, project, generated_code_dict, project_name, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateJson])
        self.project = project
        self.generated_code_dict = generated_code_dict

    async def _act(self):
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name, self.project, json_type=True)
        subprocesses = []

        dependencies = self.get_dependencies(self.generated_code_dict)
        test_groups = self.get_models_to_test(dependencies)


        test_data_path = "Tests"
        test_json_data_path = f"{test_data_path}/test_data"


        # _authentication_settings.py
        project_generator.add_file("_authentication_settings.py", f"initial_data_load = '{project_name}/{test_json_data_path}/test.json'", skip=True)


        for set_to_test in test_groups:
            set_dependencies = {d for cls in set_to_test for d in dependencies[cls]}

            class_name = '_'.join(set_to_test) + "Test"
            test_file_name = f"test_{class_name}.py"
            test_json_file_name = f"test_{class_name}.json"

            test_path = f"{test_data_path}/{test_file_name}"
            test_json_path = f"{test_json_data_path}/{test_json_file_name}"

            # Generate test for current class
            relevant_codes = self.extract_relevant_code(set_to_test, self.generated_code_dict, dependencies)

            if len(set_to_test) == 1:
                class_code = self.get_code_from_set(set_to_test, self.generated_code_dict)
                relevant_codes += "\n\n" + class_code
                set_dependencies.add(list(set_to_test)[0])

            test_import_pool = self.get_import_pool(
                project_name,
                [(cls, self.generated_code_dict[cls][0]) for cls in set_dependencies]
            )

            print(f"Generating test json for {class_name}...")

            test_json = await self.rc.todo.run(
                self.project,
                (", ".join(set_to_test), relevant_codes),
            ) + "\n\n"

            test_file = generate_test_python_jsons_alg(
                set_to_test=set_to_test,
                json_path=f"{project_name}/{test_json_path}",
            )

            project_generator.add_file(test_json_path, test_json)
            project_generator.add_file(test_path, test_file)
            subprocesses.append("{\n" + f'"subprocess": "{project_name}/{test_json_path}"' + "\n}")

        content = '[\n' + ',\n'.join(subprocesses) + "\n]"
        project_generator.add_file(f"{test_json_data_path}/test.json", content)
                
        return Message(content="Jsons generated successfully", role=self.profile, cause_by=type(self.rc.todo))


