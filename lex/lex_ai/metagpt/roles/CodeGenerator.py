import asyncio
import dataclasses
import json
import os
import ast
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Set

import networkx as nx

import django
from asgiref.sync import sync_to_async
from dataclasses import dataclass
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
from lex.lex_ai.metagpt.actions.GenerateJson import GenerateJsonRole
from lex.lex_ai.metagpt.generate_project_code import get_context_for_code_reflector, get_prompt_for_code_reflector
from lex.lex_ai.metagpt.generate_test_jsons import generate_test_python_jsons_alg
from lex.lex_ai.metagpt.roles.JsonGenerator import JsonGenerator
from lex.lex_ai.metagpt.roles.LLM import LLM
from lex.lex_ai.metagpt.roles.LexRole import LexRole
from lex.lex_ai.metagpt.roles.TestExecutor import TestExecutor
from lex.lex_app.helpers.RequestHandler import RequestHandler
from pprint import pprint

from lex_ai.metagpt.roles.CheckpointManager import CheckpointState, CodeGeneratorCheckpoint
from lex_ai.metagpt.roles.Test import TestInfo
from lex_ai.views.UserInteraction import ApprovalType, ApprovalRequest, ApprovalRegistry


class ProjectInfo:
    def __init__(self, project, project_name):
        self.project = project
        self.project_name = project_name


@dataclass
class RegenerationInfo:
    class_name: str
    previous_code: str
    code: str
    input_model_class_name: str = None
    previous_input_model_code: str = None
    input_model_code: str = None

class CodeGenerator(LexRole):
    name: str = "CodeGenerator"
    profile: str = "Expert in generating code based on architecture and specifications"

    def __init__(self, project_info, user_feedback, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateCode])
        self.project = project_info.project
        self.project_info = project_info
        self.user_feedback = user_feedback
        self.test_executor = TestExecutor(ServerManager(project_info.project_name))
        self.project_generator = ProjectGenerator(project_info.project_name, project_info.project)
        self.test_generator = ProjectGenerator(project_info.project_name, project_info.project, json_type=True)
        self.checkpoint_manager = CodeGeneratorCheckpoint(project_info.project_name)
        self.approval_registry = ApprovalRegistry()


    async def save_current_state(self, generated_code_dict: Dict[str, Any], 
                               generated_json_dict: Dict[str, str],
                               completed_tests: Set[str],
                               remaining_test_groups: List[Set[str]],
                               test_reflections: Dict[str, List[str]],
                               timestamp: datetime=None) -> datetime:
        if not timestamp:
            """Save current generation state to checkpoint"""
            state = CheckpointState(
                generated_code_dict=generated_code_dict,
                generated_json_dict=generated_json_dict,
                completed_tests=completed_tests,
                remaining_test_groups=remaining_test_groups,
                test_reflections=test_reflections,
                project_name=self.project_info.project_name
            )
        else:
            state = CheckpointState(
                generated_code_dict=generated_code_dict,
                generated_json_dict=generated_json_dict,
                completed_tests=completed_tests,
                remaining_test_groups=remaining_test_groups,
                test_reflections=test_reflections,
                project_name=self.project_info.project_name,
                timestamp=timestamp
            )

        return self.checkpoint_manager.save_checkpoint(state)

    async def restore_checkpoint(self, checkpoint_path: Optional[Path] = None) -> CheckpointState:
        """Restore state from checkpoint"""
        return self.checkpoint_manager.load_checkpoint(checkpoint_path)

    async def restore_latest_checkpoint(self) -> CheckpointState:
        latest_checkpoint = self.checkpoint_manager._get_latest_checkpoint()
        return self.checkpoint_manager.load_checkpoint(latest_checkpoint)

    # async def run_cell(self, code):
    #     code()


    async def _handle_test_failure(self, set_to_test, generated_code_dict, test_json, dependencies, response_json, test_import_pool,
                                   reflections=[]):
        correct_code_so_far = {}
        approved = False
        for class_to_test in set_to_test:
            feedback = ""
            while not approved:
                real_model_name = ""
                new_code_model = ""

                stderr_info = {
                    'test_code': test_json,
                    'class_code': self.get_code_from_set(set_to_test, generated_code_dict),
                    'error_message': response_json.get('error'),
                    'corrected_code': "\n".join(correct_code_so_far)
                }

                code_reflector = CodeReflector(
                    stderr_info,
                    self.extract_relevant_code(set_to_test, generated_code_dict, dependencies),
                    original_prompt=get_prompt_for_code_reflector(),
                    context=get_context_for_code_reflector(self.project),
                    project=self.project
                )

                reflection = await code_reflector.reflect()
                reflections.append(
                    f"------------------Reflection {len(reflections) + 1}---------------------\n\n{reflection}\n\n")

                if self.is_upload(class_to_test):
                    real_model_name = self.get_model_name(class_to_test)
                    regeneration_func = self._regenerate_code_func(real_model_name, generated_code_dict, dependencies, test_import_pool, stderr_info, feedback=feedback)
                    new_code_model = await code_reflector.regenerate("".join(reflections), regeneration_func)
                    correct_code_so_far[real_model_name] = new_code_model

                    # Update the generated code dictionary


                regeneration_func = self._regenerate_code_func(class_to_test, generated_code_dict, dependencies, test_import_pool, stderr_info, feedback=feedback)
                new_code = await code_reflector.regenerate("".join(reflections), regeneration_func)

                correct_code_so_far[class_to_test] = new_code


                regeneration_info = RegenerationInfo(
                    class_name=class_to_test,
                    previous_code=generated_code_dict[class_to_test][1],
                    code=new_code,
                    input_model_class_name=real_model_name,
                    previous_input_model_code=generated_code_dict[real_model_name][1],
                    input_model_code=new_code_model
                )

                approvalRequest = await self.request_code_regeneration_approval(regeneration_info)

                approved = approvalRequest.status
                feedback = approvalRequest.feedback
                new_code = approvalRequest.content.get("code", new_code) or new_code
                new_code_model = approvalRequest.content.get("input_model_code", new_code_model) or new_code_model

                # Update the generated code dictionary
                if approved:
                    if self.is_upload(class_to_test):
                        self.project_generator.add_file(generated_code_dict[real_model_name][0], new_code_model)
                        generated_code_dict[real_model_name] = (
                            generated_code_dict[real_model_name][0], new_code_model, generated_code_dict[real_model_name][2])

                    self.project_generator.add_file(generated_code_dict[class_to_test][0], new_code)
                    generated_code_dict[class_to_test] = (
                        generated_code_dict[class_to_test][0], new_code, generated_code_dict[class_to_test][2])

    def _regenerate_code_func(self, class_to_test, generated_code_dict, dependencies, test_import_pool, stderr_info=None, feedback=None):
        regeneration_func = lambda reflection_context: self.rc.todo.run(
            self.project,
            self.get_lex_app_context("Lex project"),
            self.extract_relevant_code(class_to_test, generated_code_dict, dependencies),
            {'class': class_to_test, 'path': generated_code_dict[class_to_test][0]},
            feedback,
            test_import_pool,
            stderr_info,
            reflection_context=reflection_context
        )

        return regeneration_func

    def is_upload(self, class_name: str) -> bool:
        return "Upload" in class_name

    def is_report(self, class_name: str) -> bool:
        return "Report" in class_name
    def get_model_name(self, class_name: str) -> str:
        return class_name.replace("Upload", "")

    async def request_code_approval(self, content: str, class_name: str) -> ApprovalRequest:
        """Request approval for generated code"""
        request_id = await self.approval_registry.create_request(
            ApprovalType.CODE_GENERATION,
            {
                'class_name': class_name,
                'code': content,
                'project_name': self.project_info.project_name
            }
        )
        await StreamProcessor.global_message_queue.put("approval_required")
        approval_request = await self.approval_registry.wait_for_approval(request_id)
        return approval_request

    async def request_code_regeneration_approval(self, regeneration_info: RegenerationInfo) -> ApprovalRequest:
        """Request approval for generated code"""
        request_id = await self.approval_registry.create_request(
            ApprovalType.CODE_REGENERATION,
            {
                **(regeneration_info.__dict__),
                'project_name': self.project_info.project_name
            }
        )
        await StreamProcessor.global_message_queue.put("approval_required")
        approval_request = await self.approval_registry.wait_for_approval(request_id)
        return approval_request

    async def request_test_approval(self, test_info: Dict[str, Any], test_code: str) -> ApprovalRequest:
        """Request approval for test implementation"""
        request_id = await self.approval_registry.create_request(
            ApprovalType.TEST_GENERATION,
            {
                'test_name': test_info['class_name'],
                'test_code': test_code,
                'test_json': test_info.get('test_json'),
                'dependencies': test_info.get('dependencies', [])
            }
        )
        await StreamProcessor.global_message_queue.put("approval_required")
        approval_request = await self.approval_registry.wait_for_approval(request_id)
        return approval_request

    async def request_test_after_execution_approval(self, test_info: TestInfo, test_result: Dict[str, Any]) -> ApprovalRequest:
        """Request approval for test execution results"""
        request_id = await self.approval_registry.create_request(
            ApprovalType.TEST_AFTER_EXECUTION,
            {
                **(test_info.__dict__),
                'success': test_result['success'],
                'error': test_result.get('error'),
                'console_output': test_result.get('console_output', {}),
            }
        )
        await StreamProcessor.global_message_queue.put("approval_required")
        approval_request = await self.approval_registry.wait_for_approval(request_id)
        return approval_request

    async def request_test_execution_approval(self, test_info: TestInfo) -> ApprovalRequest:
        """Request approval for test execution"""
        request_id = await self.approval_registry.create_request(
            ApprovalType.TEST_EXECUTION,
            test_info.__dict__
        )
        await StreamProcessor.global_message_queue.put("approval_required")
        approval_request = await self.approval_registry.wait_for_approval(request_id)
        return approval_request

    async def generate_class(self, lex_app_context, generated_code_dict, class_to_generate, import_pool, user_feedback):
        code = await self.rc.todo.run(
            self.project,
            lex_app_context,
            self._combine_code(generated_code_dict),
            class_to_generate=class_to_generate,
            import_pool=import_pool,
            user_feedback=user_feedback,
        ) + "\n\n"
        return code


    async def _act(self) -> Message:
        project_name = self.project_info.project_name
        try:
            shutil.rmtree(project_name)
        except OSError as e:
            pass

        project_generator = self.project_generator
        test_generator = self.test_generator

        await project_generator._create_base_structure()
        lex_app_context = self.get_lex_app_context("Lex project")
        all_classes = list(self.project.classes_and_their_paths.items())
        import_pool = self.get_import_pool(project_name, all_classes)

        timestamp = None
        generated_code_dict = {}  # Dictionary to store class_name: (path, code)

    # ------------------------------------------------------------------------------
        try:
            checkpoint_state = await self.restore_latest_checkpoint()
            generated_code_dict = checkpoint_state.generated_code_dict
            generated_json_dict = checkpoint_state.generated_json_dict
            completed_tests = checkpoint_state.completed_tests
            timestamp = checkpoint_state.timestamp


            for class_name, (path, code, _) in generated_code_dict.items():
                project_generator.add_file(path, code)

            for class_name, info in generated_json_dict.items():
                subprocess_path = info[0]
                subprocess_json = info[1]
                json_path = info[2]
                json_code = info[3]
                py_path = info[4]
                py_code = info[5]

                test_generator.add_file(json_path, json_code)
                test_generator.add_file(subprocess_path, subprocess_json)
                test_generator.add_file(py_path, py_code)

            # Verify all files exist and regenerate missing ones
            for class_to_generate in all_classes:
                class_name, path = class_to_generate
                full_path = Path(project_name) / path
                if not full_path.exists():
                    class_to_generate = next((c for c in all_classes if c[0] == class_name), None)
                    if class_to_generate:
                        approved = False
                        user_feedback = ""
                        while not approved or not ApprovalRegistry.APPROVAL_ON:
                            await StreamProcessor.global_message_queue.put(f"code_file_path:{path}\n")
                            code = await self.generate_class(
                                lex_app_context=lex_app_context,
                                generated_code_dict=generated_code_dict,
                                class_to_generate=class_to_generate,
                                import_pool=import_pool,
                                user_feedback=user_feedback,
                            )
                            parsed_code = list(project_generator.parse_codes_with_filenames(code).items())[0][1]
                            generated_code_dict[class_name] = (
                            path, code, self.extract_project_imports(parsed_code, project_name))

                            approvalRequest = await self.request_code_approval(code, class_name)
                            approved = approvalRequest.status
                            user_feedback = approvalRequest.feedback
                            code = approvalRequest.content["code"]

                        project_generator.add_file(path, code)
                        timestamp = await self.save_current_state(
                            generated_code_dict,
                            generated_json_dict,
                            completed_tests,
                            [],
                            {},
                            timestamp
                        )


        except FileNotFoundError:
            # Start fresh if no checkpoint exists
            generated_code_dict = {}
            generated_json_dict = {}
            completed_tests = set()

            # Generate all classes
            for class_to_generate in all_classes:
                approved = False
                user_feedback = ""
                path = ""
                parsed_code = ""
                class_name = ""
                while not approved or not ApprovalRegistry.APPROVAL_ON:
                    class_name, path = class_to_generate
                    path = path.replace('\\', '/').strip('/')

                    await StreamProcessor.global_message_queue.put(f"code_file_path:{path}\n")
                    code = await self.generate_class(
                        lex_app_context=lex_app_context,
                        generated_code_dict=generated_code_dict,
                        class_to_generate=class_to_generate,
                        import_pool=import_pool,
                        user_feedback=user_feedback
                    )

                    parsed_code = list(project_generator.parse_codes_with_filenames(code).items())[0][1]

                    approvalRequest = await self.request_code_approval(code, class_name)
                    approved = approvalRequest.status
                    user_feedback = approvalRequest.feedback
                    code = approvalRequest.content["code"]

                generated_code_dict[class_name] = (path, code, self.extract_project_imports(parsed_code, project_name))
                project_generator.add_file(path, code)
                # Save checkpoint after each class generation
                timestamp = await self.save_current_state(
                    generated_code_dict,
                    generated_json_dict,
                    completed_tests,
                    [],
                    {},
                    timestamp
                )

        max_attempts = 5

        subprocesses = []
        test_data_path = "Tests"
        test_json_data_path = f"{test_data_path}/test_data"

# ------------------------------------------------------------------------------
        redirected_dependencies = self.get_dependencies_redirected(generated_code_dict)
        dependencies = self.get_dependencies(generated_code_dict)
        test_groups = self.get_models_to_test(redirected_dependencies)
        remaining_tests = [group for group in test_groups
                           if "_".join(group) not in completed_tests]

        skipped_tests = []

        for set_to_test in remaining_tests:
            set_dependencies = {d for cls in set_to_test for d in redirected_dependencies[cls]}

            reflections = []
            attempts = 0
            success = False
            combined_class_name = "_".join(set_to_test)

            class_name = combined_class_name + "Test"
            test_file_name = f"test_{class_name}.py"
            test_json_file_name = f"{class_name}.json"

            test_path = f"{test_data_path}/{test_file_name}"
            test_json_path = f"{test_json_data_path}/{test_json_file_name}"

            upload = False
            relevant_codes = self.extract_relevant_code(set_to_test, generated_code_dict, dependencies)

            if len(set_to_test) == 1:
                class_code = self.get_code_from_set(set_to_test, generated_code_dict)
                relevant_codes += "\n\n" + class_code
                set_dependencies.add(list(set_to_test)[0])
                upload = self.is_upload(next(iter(set_to_test)))

            test_import_pool = self.get_import_pool(
                project_name,
                [(cls, generated_code_dict[cls][0]) for cls in set_dependencies]
            )
            relevant_json = self.extract_relevant_json(set_to_test, generated_json_dict, redirected_dependencies)


            print(f"Generating test json for {class_name}...")

            number_of_objects_for_report = None
            if self.is_report(combined_class_name):
                number_of_objects_for_report = 1



            approved = False
            user_feedback = ""
            # Test approval
            while not approved or not ApprovalRegistry.APPROVAL_ON:
                await StreamProcessor.global_message_queue.put(f"code_file_path:{test_json_path}\n")

                test_json = (await (GenerateJsonRole(
                    self.project,
                    (", ".join(set_to_test), relevant_codes),
                    relevant_json,
                    number_of_objects_for_report=number_of_objects_for_report,
                    user_feedback=user_feedback
                ).run("START"))).content + "\n\n"

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

                approvalRequest  = await self.request_test_approval({
                    'class_name': class_name,
                    'test_json': test_json,
                    'dependencies': list(set_dependencies)
                }, test_file)

                approved = approvalRequest
                user_feedback = approvalRequest.feedback
                content = approvalRequest.content

                test_json = content.get("test_json", None) or test_json
                test_file = content.get("test_code", None) or test_file


            sub_subprocesses = self.get_models_to_test(self.get_relevant_dependency_dict(combined_class_name, redirected_dependencies))
            helper = lambda x: "{\n\t" + f'"subprocess" : "{self.get_test_path(test_json_data_path, x, project_name)}"' + "\n}"
            sub_subprocesses = [helper(subprocess) for subprocess in sub_subprocesses]
            subprocesses.append(helper(combined_class_name))
            content = '[\n' + ',\n'.join(sub_subprocesses) + "\n]"


            generated_json_dict[combined_class_name] = start_test_path, content, test_json_path, test_json, test_path, test_file

            test_generator.add_file(test_json_path, test_json)
            await test_generator.add_file_and_stream(start_test_path, content, queue=StreamProcessor.global_message_queue)
            await test_generator.add_file_and_stream(test_path, test_file, queue=StreamProcessor.global_message_queue)

    # ------------------------------------------------------------------------------
            test_info = TestInfo(
                test_json_path=test_json_path,
                test_file_path=test_path,
                test_name=combined_class_name,
                test_code={
                    "json": test_json,
                    "python": test_file
                },
                dependencies=list(set_dependencies),
                project_name=project_name,
                set_to_test=set_to_test
            )


            while len(skipped_tests) == 0 and not success and attempts < max_attempts:

                response = await self.test_executor.execute_test(test_file_name, project_name)
                success = response['success']


                approvalRequest = await self.request_test_after_execution_approval(test_info, response)
                approved = approvalRequest.status

                if not approved:
                    if not success:
                        await self._handle_test_failure(
                            set_to_test,
                            generated_code_dict,
                            test_json,
                            dependencies,
                            response,
                            test_import_pool,
                            reflections
                        )
                        attempts += 1
                    else:
                        completed_tests.add("_".join(set_to_test))
                        # Save checkpoint after successful test

                        timestamp = await self.save_current_state(
                            generated_code_dict,
                            generated_json_dict,
                            completed_tests,
                            remaining_tests,
                            {class_name: reflections},
                            timestamp
                        )
                else:
                    if not success:
                        skipped_tests.append(combined_class_name)

        # Generate final test configuration
        content = '[\n' + ',\n'.join(subprocesses) + "\n]"
        await test_generator.add_file_and_stream(
            f"{test_json_data_path}/test.json",
            content,
            queue=StreamProcessor.global_message_queue
        )

        content = '[\n' + ',\n'.join(subprocesses) + "\n]"
        test_all_path = f"{test_data_path}/test.py"
        test_all = generate_test_python_jsons_alg(
            set_to_test={""},
            json_path=f"{project_name}/{test_json_data_path}/test.json"
        )
        #
        await test_generator.add_file_and_stream(f"{test_json_data_path}/test.json", content, queue=StreamProcessor.global_message_queue)
        await test_generator.add_file_and_stream("_authentication_settings.py", f"initial_data_load = '{project_name}/{test_json_data_path}/test.json'", queue=StreamProcessor.global_message_queue)
        await test_generator.add_file_and_stream(test_all_path, test_all, queue=StreamProcessor.global_message_queue)

        print("--------------------------------------------\n")


        response = await self.test_executor.execute_test("test.py", project_name)

        await self.save_current_state(
            generated_code_dict,
            generated_json_dict,
            completed_tests,
            remaining_tests,
            [],
            timestamp
        )
        # Return results
        message = Message(
            content=self._combine_code(generated_code_dict),
            role=self.profile,
            cause_by=type(self.rc.todo),
        )
        return message

