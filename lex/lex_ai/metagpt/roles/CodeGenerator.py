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
from lex_ai.metagpt.actions.GenerateCode import GenerateCode
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

class CodeGenerator(Role):
    name: str = "CodeGenerator"
    profile: str = "Expert in generating code based on architecture and specifications"

    def __init__(self, project, user_feedback, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateCode])
        self.project = project
        self.user_feedback = user_feedback


    # async def _act(self) -> Message:
    #     print("-----------------------------------------------------------------------------------------------------")
    #     print("------------------------------------Code Generator---------------------------------------------------")
    #     project_name = "__DemoWindparkConsolidation"
    #     project_generator = ProjectGenerator(project_name)
    #
    #     lex_app_context = self.get_lex_app_context("Lex project")
    #     classes_to_generate = self.project.classes_and_their_paths.items()
    #
    #     import_pool = "\n".join([f"Class {class_name}\n\tImporPath:from {project_name}.{path.replace(os.sep, '.').rstrip('.py')} import {class_name}" for class_name, path in classes_to_generate])
    #
    #     success = False
    #     test_results = None
    #     stderr = None
    #     generated_code = ""
    #     test_code = ""
    #
    #
    #     while classes_to_generate:
    #         generated_code = ""
    #         test_code = ""
    #         for class_to_generate in classes_to_generate:
    #             path = class_to_generate[1].replace('\\', '/').strip('/')
    #             await StreamProcessor.global_message_queue.put(f"code_file_path:{path}\n")
    #             code = await self.rc.todo.run(self.project, lex_app_context,
    #                                           generated_code, class_to_generate, self.user_feedback, import_pool, stderr) + "\n\n"
    #
    #             print("Classes to generate: ", class_to_generate)
    #             project_generator.add_file(class_to_generate[1], code)
    #             generated_code += code
    #
    #         call_command("makemigrations")
    #         call_command("migrate")
    #
    #         for class_to_generate in classes_to_generate:
    #             success = False
    #             test = await generate_test_for_code(generated_code, self.project, import_pool, class_to_generate, test_code)
    #             path = class_to_generate[1].replace('\\', '/').strip('/')
    #             await StreamProcessor.global_message_queue.put(f"code_file_path:Tests/{path}\n")
    #             project_generator.add_file("Tests/test_" + class_to_generate[0] + "Test.py", test)
    #
    #             while not success:
    #                 response_data = run_tests(project_name, test_file="test_" + class_to_generate[0] + "Test.py")
    #                 success = response_data.get("success")
    #                 test_results = response_data.get("test_results")
    #                 stderr = response_data.get("console_output").get("stderr")
    #                 classes_to_generate = get_failed_test_classes(stderr)
    #                 if not classes_to_generate:
    #                     break
    #                 generated_code += test
    #
    #             test_code += test
    #
    #         response_data = run_tests(project_name)
    #         success = response_data.get("success")
    #         test_results = response_data.get("test_results")
    #         stderr = response_data.get("console_output").get("stderr")
    #         classes_to_generate = get_failed_test_classes(stderr)
    #
    #
    #     message = Message(content=generated_code, role=self.profile, cause_by=type(self.rc.todo))
    #     return message


    def extract_project_imports(self, code_string, project_name):
        result = []
        tree = ast.parse(code_string)

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module_path = node.module
                if module_path and module_path.startswith(project_name):
                    # Split the module path and get the last component (class name)
                    imported_class = node.names[0].name
                    result.append(imported_class)

        return result

    def get_dependencies(self, generated_code_dict):
        return {k: v for k, (_, _, v) in generated_code_dict.items()}

    def get_models_to_test(self, dependencies):
        G = nx.DiGraph(dependencies)

        sccs = list(nx.strongly_connected_components(G))
        return sccs

    def extract_relevant_code(self, class_set, generated_code_dict, dependencies):
        if isinstance(class_set, str):
            class_set = {class_set}

        all_dependent_classes = {d for cls in class_set for d in dependencies[cls]}


        return "\n\n".join([f"### {generated_code_dict[cls][0]}\n{generated_code_dict[cls][1]}" for cls in all_dependent_classes])

    def get_code_from_set(self, class_set, generated_code_dict):
        if isinstance(class_set, str):
            class_set = {class_set}

        return "\n\n".join([generated_code_dict[cls][1] for cls in class_set])


    def get_import_pool(self, project_name, all_classes):
        # Generate import pool
        import_pool = "\n".join([
            f"Inner ImporPath: from {project_name}.{path.replace(os.sep, '.').rstrip('.py')} import {class_name}"
            for class_name, path in all_classes
        ])
        import_pool += "\nExternal ImportPath: from django.db import models"
        import_pool += "\nExternal ImportPath: import pandas as pd"
        import_pool += "\nExternal ImportPath: import numpy as np"

        return import_pool

    async def _act(self) -> Message:
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name, self.project)
        await project_generator._create_base_structure()
        lex_app_context = self.get_lex_app_context("Lex project")
        all_classes = list(self.project.classes_and_their_paths.items())

        import_pool = self.get_import_pool(project_name, all_classes)

        # Step 1: Generate all classes first
        generated_code_dict = {}  # Dictionary to store class_name: (path, code)

        for class_to_generate in all_classes:
            class_name, path = class_to_generate
            path = path.replace('\\', '/').strip('/')
            await StreamProcessor.global_message_queue.put(f"code_file_path:{path}\n")

            code = await self.rc.todo.run(
                self.project,
                lex_app_context,
                self._combine_code(generated_code_dict),  # Combine all existing code
                class_to_generate,
                self.user_feedback,
                import_pool,
            ) + "\n\n"

            project_generator.add_file(path, code)
            parsed_code = list(project_generator.parse_codes_with_filenames(code).items())[0][1]
            generated_code_dict[class_name] = (path, code, self.extract_project_imports(parsed_code, project_name))

        server_manager = ServerManager(project_name)
        server_obj = server_manager.restart_server()

        while not server_obj.is_alive():
            time.sleep(0.1)

        time.sleep(2)
        try:
            request_handler = RequestHandler(max_retries=3, timeout=10, retry_delay=2)
            response = request_handler.post_with_retry("http://127.0.0.1:8001/ai/run-migrations/", {"project_name": project_name})
            if response is None:
                print("Failed to get response after all retries")

            response_data = response.json()
            success = response_data.get("success")
            if not success:
                print("Failed to run migrations")
                raise RequestException

        except RequestException as e:
            print(f"Request failed: {str(e)}")
            raise

        # Step 2: Generate and test each class, regenerating if tests fail
        max_attempts = 3
        
        dependencies = self.get_dependencies(generated_code_dict)
        test_groups = self.get_models_to_test(dependencies)


        print("Dependencies: ", dependencies)
        print("Test groups: ", test_groups)

        for set_to_test in test_groups:
            set_dependencies = {d for cls in set_to_test for d in dependencies[cls]}
            attempts = 0
            success = False

            class_name = '_'.join(set_to_test) + "Test"
            test_file_name = f"test_{class_name}.py"
            test_path = f"Tests/{test_file_name}"

            # Generate test for current class
            relevant_codes = self.extract_relevant_code(set_to_test, generated_code_dict, dependencies)

            if len(set_to_test) == 1:
                class_code = self.get_code_from_set(set_to_test, generated_code_dict)
                relevant_codes += "\n\n" + class_code
                set_dependencies.add(list(set_to_test)[0])

            test_import_pool = self.get_import_pool(
                project_name,
                [(cls, generated_code_dict[cls][0]) for cls in set_dependencies]
            )

            print("Test import pool: ", test_import_pool)

            test = await generate_test_for_code(
                relevant_codes,
                self.project,
                test_import_pool,
                set_to_test,
                class_name,
                set_dependencies
            )

            # Add test file
            project_generator.add_file(test_path, test)
            await StreamProcessor.global_message_queue.put(f"code_file_path:{test_path}\n")

            while not success and attempts < max_attempts:
                server_obj = server_manager.restart_server()

                while not server_obj.is_alive():
                    time.sleep(0.1)
                
                time.sleep(2)
                
                data = {
                    'test_file_name': test_file_name,
                    'project_name': project_name
                }

                try:
                    request_handler = RequestHandler(max_retries=3, timeout=10, retry_delay=2)
                    response = request_handler.post_with_retry("http://127.0.0.1:8001/ai/run-test/", data)
                    if response is None:
                        print("Failed to get response after all retries")
                        success = False
                        continue

                    response_data = response.json()
                    pprint(response_data)
                    success = response_data.get("success")

                except RequestException as e:
                    print(f"Request failed: {str(e)}")
                    success = False
                    attempts += 1
                    continue

                if not success:
                    correct_code_so_far = {}
                    # If test failed, regenerate the class
                    for class_to_test in set_to_test:
                        stderr_info = {
                            'test_code': test,
                            'class_code': self.get_code_from_set(set_to_test, generated_code_dict),
                            'error_message': response_data.get("console_output", {}).get("stderr", [])
                        }
                        stderr_info['corrected_code'] = "\n".join(correct_code_so_far)

                        # Regenerate the failed class
                        new_code = await self.rc.todo.run(
                            self.project,
                            lex_app_context,
                            relevant_codes,
                            {'class': class_to_test, 'path': generated_code_dict[class_to_test][0]},
                            self.user_feedback,
                            test_import_pool,
                            stderr_info
                        ) + "\n\n"
                        correct_code_so_far[class_to_test] = new_code

                        # Update the generated code dictionary
                        project_generator.add_file(generated_code_dict[class_to_test][0], new_code)
                        generated_code_dict[class_to_test] = (generated_code_dict[class_to_test][0], new_code, generated_code_dict[class_to_test][2])

                    attempts += 1
                else:
                    break

        # Return results
        message = Message(
            content=self._combine_code(generated_code_dict),
            role=self.profile,
            cause_by=type(self.rc.todo),
        )
        return message

    def _combine_code(self, code_dict: dict) -> str:
        """Combines all code from the dictionary into a single string."""
        return "\n\n".join([
            f"### {t[0]}\n{t[1]}"
            for _, t in code_dict.items()
        ])
    def get_lex_app_context(self, prompt):
        rag = RAG()
        i, j = rag.memorize_dir(RAG.LEX_APP_DIR)

        # lex_app_context = "\n".join([rag.query_code("LexModel", i, j, top_k=1)[0],
        #                              rag.query_code("CalculationModel", i, j, top_k=1)[0],
        #                              rag.query_code("LexLogger", i, j, top_k=1)[0],
        #                              rag.query_code("XLSXField", i, j, top_k=1)[0]])
        lex_app_context = "\n".join(rag.query_code("LexModel, CalculationModel, XLSXField, LexLogger", i, j, top_k=30))


        return lex_app_context
