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
from lex.lex_ai.metagpt.generate_test_for_code import generate_test_for_code
from lex.lex_ai.metagpt.run_tests import run_tests, get_failed_test_classes
from lex_app.helpers.RequestHandler import RequestHandler
from pprint import pprint




class JsonGenerator(Role):
    name: str = "JsonGenerator"
    profile: str = "Expert in generating test jsons"

    def __init__(self, project, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateJson])
        self.project = project

    
    async def _act(self):
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name, self.project, json_type=True)
        # all_classes = list(self.project.classes_and_their_paths.items())
        all_code = extract_python_code_from_directory("DemoWindparkConsolidation")
        all_classes = [(k, v['path'], v['content']) for k, v in all_code.items()] # (class_name, path, code)


        for test_json_to_generate in all_classes:
            class_name, _, content = test_json_to_generate

            path = f"test_data/test_{class_name}.json"

            print(f"Generating test json for {class_name}...")
            test_json = await self.rc.todo.run(
                self.project,
                test_json_to_generate,
            ) + "\n\n"
            project_generator.add_file(path, test_json)




def extract_python_code_from_directory(directory_path):
    python_code_files = {}

    # Iterate over all files in the directory
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Check if the file has a .py extension
            if (file.endswith(".py")
                    and not file.startswith("test_")
                    and not file.startswith("0")
                    and not file.startswith("_")):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract Python code using parse_code
                    extracted_code = content
                    # Add to dictionary with file name as key
                    python_code_files[file.split(".")[0]] = {"content": extracted_code, "path": file_path.split("./projects/")[-1]}

    return python_code_files