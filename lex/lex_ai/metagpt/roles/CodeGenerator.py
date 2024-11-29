import asyncio
import json
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
from lex_ai.metagpt.actions.CodeReflector import CodeReflector
from lex_ai.metagpt.actions.GenerateCode import GenerateCode
from lex.lex_app.helpers.run_server import ServerManager
from metagpt.schema import Message
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts

from metagpt.roles.role import Role
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex.lex_ai.metagpt.generate_test_for_code import generate_test_for_code
from lex.lex_ai.metagpt.run_tests import run_tests, get_failed_test_classes
from lex_ai.metagpt.actions.GenerateJson import GenerateJsonRole
from lex_ai.metagpt.generate_project_code import get_context_for_code_reflector, get_prompt_for_code_reflector
from lex_ai.metagpt.generate_test_jsons import generate_test_python_jsons_alg
from lex_ai.metagpt.roles.JsonGenerator import JsonGenerator
from lex_ai.metagpt.roles.LLM import LLM
from lex_ai.metagpt.roles.LexRole import LexRole
from lex_app.helpers.RequestHandler import RequestHandler
from pprint import pprint



class CodeGenerator(LexRole):
    name: str = "CodeGenerator"
    profile: str = "Expert in generating code based on architecture and specifications"

    def __init__(self, project, user_feedback, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateCode])
        self.project = project
        self.user_feedback = user_feedback


    def is_upload(self, class_name: str) -> bool:
        return "Upload" in class_name

    def is_report(self, class_name: str) -> bool:
        return "Report" in class_name
    def get_model_name(self, class_name: str) -> str:
        return class_name.replace("Upload", "")

    async def _act(self) -> Message:
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name, self.project)
        await project_generator._create_base_structure()
        lex_app_context = self.get_lex_app_context("Lex project")
        all_classes = list(self.project.classes_and_their_paths.items())

        import_pool = self.get_import_pool(project_name, all_classes)

        # Step 1: Generate all classes first
        generated_code_dict = {}  # Dictionary to store class_name: (path, code)
        cache = True



        if not cache:
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
        else:
            generated_code_dict = self.extract_python_code_from_directory(project_name)

        server_manager = ServerManager(project_name)
        # server_obj = server_manager.restart_server()
        #
        # while not server_obj.is_alive():
        #     time.sleep(0.1)
        #
        # time.sleep(2)
        # try:
        #     request_handler = RequestHandler(max_retries=3, timeout=10, retry_delay=2)
        #     response = request_handler.post_with_retry("http://127.0.0.1:8001/ai/run-migrations/", {"project_name": project_name})
        #     if response is None:
        #         print("Failed to get response after all retries")
        #
        #     response_data = response.json()
        #     success = response_data.get("success")
        #     if not success:
        #         print("Failed to run migrations")
        #         raise RequestException
        #
        # except RequestException as e:
        #     print(f"Request failed: {str(e)}")
        #     raise

        # Step 2: Generate and test each class, regenerating if tests fail
        max_attempts = 5
        
        # dependencies = self.get_dependencies(generated_code_dict)
        # test_groups = self.get_models_to_test(dependencies)


        # print("Dependencies: ", dependencies)
        # print("Test groups: ", test_groups)

        test_generator = ProjectGenerator(project_name, self.project, json_type=True)

        redirected_dependencies = self.get_dependencies_redirected(generated_code_dict)
        dependencies = self.get_dependencies(generated_code_dict)
        test_groups = self.get_models_to_test(redirected_dependencies)

        subprocesses = []

        test_data_path = "Tests"
        test_json_data_path = f"{test_data_path}/test_data"

        generated_json_dict = {}

        for set_to_test in test_groups:
            reflections = []
            set_dependencies = {d for cls in set_to_test for d in redirected_dependencies[cls]}
            attempts = 0
            success = False

            combined_class_name = "_".join(set_to_test)

            class_name = combined_class_name + "Test"
            test_file_name = f"test_{class_name}.py"
            test_json_file_name = f"{class_name}.json"

            test_path = f"{test_data_path}/{test_file_name}"
            test_json_path = f"{test_json_data_path}/{test_json_file_name}"

            # Generate test for current class
            relevant_codes = self.extract_relevant_code(set_to_test, generated_code_dict, dependencies)
            upload = False

            if len(set_to_test) == 1:
                class_code = self.get_code_from_set(set_to_test, generated_code_dict)
                relevant_codes += "\n\n" + class_code
                set_dependencies.add(list(set_to_test)[0])
                upload = self.is_upload(next(iter(set_to_test)))

            test_import_pool = self.get_import_pool(
                project_name,
                [(cls, generated_code_dict[cls][0]) for cls in set_dependencies]
            )

            print("Test import pool: ", test_import_pool)

            relevant_json = self.extract_relevant_json(set_to_test, generated_json_dict, redirected_dependencies)

            # test = await generate_test_for_code(
            #     relevant_codes,
            #     self.project,
            #     test_import_pool,
            #     set_to_test,
            #     class_name,
            #     set_dependencies
            # )

            print(f"Generating test json for {class_name}...")

            number_of_objects_for_report = None
            if self.is_report(combined_class_name):
                number_of_objects_for_report = 1

            await StreamProcessor.global_message_queue.put(f"code_file_path:{test_json_path}\n")
            test_json = (await (GenerateJsonRole(
                self.project,
                (", ".join(set_to_test), relevant_codes),
                relevant_json,
                number_of_objects_for_report=number_of_objects_for_report
            ).run("START"))).content + "\n\n"

            generated_json_dict[combined_class_name] = test_json

            sub_subprocesses = self.get_models_to_test(self.get_relevant_dependency_dict(combined_class_name, redirected_dependencies))
            helper = lambda x: "{\n\t" + f'"subprocess" : "{self.get_test_path(test_json_data_path, x, project_name)}"' + "\n}"
            sub_subprocesses = [helper(subprocess) for subprocess in sub_subprocesses]
            subprocesses.append(helper(combined_class_name))
            content = '[\n' + ',\n'.join(sub_subprocesses) + "\n]"
            start_test_path = f"{test_json_data_path}/test_{combined_class_name}.json"

            path_to_input_file = ""

            for parameter in list(json.loads(test_json)[0]['parameters'].values()):
                if isinstance(parameter, str) and parameter.startswith(project_name):
                    path_to_input_file = parameter
                    break


            if upload:
                test_file = generate_test_python_jsons_alg(
                    set_to_test=set_to_test,
                    json_path=f"{project_name}/{start_test_path}",
                    upload=True,
                    path_to_file_input=path_to_input_file,
                )
            else:
                test_file = generate_test_python_jsons_alg(
                    set_to_test=set_to_test,
                    json_path=f"{project_name}/{start_test_path}",
                )

            test_generator.add_file(test_json_path, test_json)
            await test_generator.add_file_and_stream(start_test_path, content, queue=StreamProcessor.global_message_queue)
            await test_generator.add_file_and_stream(test_path, test_file, queue=StreamProcessor.global_message_queue)

            while not success and attempts < max_attempts:
                server_obj = server_manager.restart_server()

                while not server_obj.is_alive() and not server_obj.is_migration_setup_error():
                    time.sleep(0.1)

                if server_obj.is_migration_setup_error():
                    response_json = json.loads(server_obj.shared_state['exit'])
                    success = False
                else:
                    time.sleep(3)
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
                        response_json = response.json()
                        print("\n".join(response_json['console_output']['stderr']))

                        success = response_json.get("success")
                        response_data = self.extract_test_failures(response_json)

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
                            'test_code': test_json,
                            'class_code': self.get_code_from_set(set_to_test, generated_code_dict),
                            'error_message': "\n".join(response_json['console_output']['stderr']),
                        }

                        stderr_info['corrected_code'] = "\n".join(correct_code_so_far)

                        context = get_context_for_code_reflector(self.project)
                        original_prompt = get_prompt_for_code_reflector()
                        code_reflector = CodeReflector(stderr_info, relevant_codes, original_prompt=original_prompt, context=context, project=self.project)
                        reflection = await code_reflector.reflect()

                        reflections.append(f"------------------Reflection {len(reflections)+1}---------------------\n\n{reflection}\n\n")

                        if self.is_upload(class_to_test):
                            real_model_name = self.get_model_name(class_to_test)
                            func = lambda reflection_context: self.rc.todo.run(
                                self.project,
                                lex_app_context,
                                relevant_codes,
                                {'class': real_model_name, 'path': generated_code_dict[real_model_name][0]},
                                self.user_feedback,
                                test_import_pool,
                                stderr_info,
                                reflection_context=reflection_context
                            )

                            new_code = await code_reflector.regenerate("".join(reflections), func)
                            correct_code_so_far[real_model_name] = new_code

                            # Update the generated code dictionary
                            project_generator.add_file(generated_code_dict[real_model_name][0], new_code)
                            generated_code_dict[real_model_name] = (generated_code_dict[real_model_name][0], new_code, generated_code_dict[real_model_name][2])

                        relevant_codes = self.extract_relevant_code(set_to_test, generated_code_dict, dependencies)
                        # Regenerate the failed class
                        regeneration_func = lambda reflection_context: self.rc.todo.run(
                            self.project,
                            lex_app_context,
                            relevant_codes,
                            {'class': class_to_test, 'path': generated_code_dict[class_to_test][0]},
                            self.user_feedback,
                            test_import_pool,
                            stderr_info,
                            reflection_context=reflection_context
                        )


                        new_code = await code_reflector.regenerate("".join(reflections), regeneration_func)
                        correct_code_so_far[class_to_test] = new_code

                        # Update the generated code dictionary
                        project_generator.add_file(generated_code_dict[class_to_test][0], new_code)
                        generated_code_dict[class_to_test] = (generated_code_dict[class_to_test][0], new_code, generated_code_dict[class_to_test][2])

                    attempts += 1
                else:
                    break

        content = '[\n' + ',\n'.join(subprocesses) + "\n]"
        test_all_path = f"{test_data_path}/test.py"
        test_all = generate_test_python_jsons_alg(
            set_to_test={""},
            json_path=f"{project_name}/{test_json_data_path}/test.json"
        )

        await test_generator.add_file_and_stream(f"{test_json_data_path}/test.json", content, queue=StreamProcessor.global_message_queue)
        await test_generator.add_file_and_stream("_authentication_settings.py", f"initial_data_load = '{project_name}/{test_json_data_path}/test.json'", queue=StreamProcessor.global_message_queue)
        await test_generator.add_file_and_stream(f"{test_data_path}/test.py", test_all, queue=StreamProcessor.global_message_queue)

        print("--------------------------------------------\n")

        print("Running all tests...\n")

        server_obj = server_manager.restart_server()

        while not server_obj.is_alive():
            time.sleep(0.1)

        time.sleep(2)

        data = {
            'test_file_name': f"test.py",
            'project_name': project_name
        }
        # Step 3: Run all tests
        try:
            request_handler = RequestHandler(max_retries=3, timeout=10, retry_delay=2)
            response = request_handler.post_with_retry("http://127.0.0.1:8001/ai/run-test/", data)
            if response is None:
                print("Failed to get response after all retries")
            response_json = response.json()
            print("\n".join(response_json['console_output']['stderr']))

            response_data = self.extract_test_failures(response_json)

        except RequestException as e:
            print(f"Request failed: {str(e)}")

        # Return results
        message = Message(
            content=self._combine_code(generated_code_dict),
            role=self.profile,
            cause_by=type(self.rc.todo),
        )
        return message

