import json
import time

from lex_ai.helpers.StreamProcessor import StreamProcessor
from lex_ai.metagpt.ProjectGenerator import ProjectGenerator
from lex_ai.metagpt.actions.CodeReflector import CodeReflector
from lex_ai.metagpt.actions.GenerateCode import GenerateCode
from lex_ai.metagpt.actions.GenerateJson import GenerateJsonRole
from lex_ai.metagpt.generate_project_code import get_prompt_for_code_reflector, get_context_for_code_reflector
from lex_ai.metagpt.generate_test_jsons import generate_test_python_jsons_alg
from lex_ai.metagpt.roles.LexRole import LexRole
from lex_app.helpers.RequestHandler import RequestHandler
from lex_app.helpers.run_server import ServerManager


class TestExecutor:
    def __init__(self, server_manager, request_handler=None):
        self.server_manager = server_manager
        self.request_handler = request_handler or RequestHandler(max_retries=3, timeout=10, retry_delay=2)

    async def execute_test(self, test_file_name, project_name):
        server_obj = self.server_manager.restart_server()

        while not server_obj.is_alive() and not server_obj.is_migration_setup_error():
            time.sleep(0.1)

        if server_obj.is_migration_setup_error():
            return {
                'success': False,
                'response_json': json.loads(server_obj.shared_state['exit'])
            }

        time.sleep(3)
        return await self._send_test_request(test_file_name, project_name)

    async def _send_test_request(self, test_file_name, project_name):
        data = {
            'test_file_name': test_file_name,
            'project_name': project_name
        }
        try:
            response = self.request_handler.post_with_retry("http://127.0.0.1:8001/ai/run-test/", data)
            if response is None:
                return {'success': False}

            response_json = response.json()
            print("\n".join(response_json['console_output']['stderr']))
            return {
                'success': response_json.get("success"),
                'response_json': response_json
            }
        except RequestException as e:
            print(f"Request failed: {str(e)}")
            return {'success': False}


class CodeGenerator(LexRole):
    def __init__(self, project, user_feedback, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateCode])
        self.project = project
        self.user_feedback = user_feedback
        self.server_manager = ServerManager(project.name)
        self.test_executor = TestExecutor(self.server_manager)
        self.project_generator = ProjectGenerator(project.name, project)
        self.max_attempts = 5

    async def _handle_test_failure(self, set_to_test, generated_code_dict, test_json, dependencies, response_json, reflections=[]):
        correct_code_so_far = {}
        for class_to_test in set_to_test:
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
            reflections.append(f"------------------Reflection {len(reflections)+1}---------------------\n\n{reflection}\n\n")


            if self.is_upload(class_to_test):
                real_model_name = self.get_model_name(class_to_test)
                regeneration_func = self._regenerate_code_func(real_model_name, generated_code_dict, dependencies)
                new_code = await code_reflector.regenerate("".join(reflections), regeneration_func)
                correct_code_so_far[real_model_name] = new_code

                # Update the generated code dictionary
                self.project_generator.add_file(generated_code_dict[real_model_name][0], new_code)
                generated_code_dict[real_model_name] = (
                generated_code_dict[real_model_name][0], new_code, generated_code_dict[real_model_name][2])


            regeneration_func = self._regenerate_code_func(class_to_test, generated_code_dict, dependencies)
            new_code = await code_reflector.regenerate("".join(reflections), regeneration_func)

            correct_code_so_far[class_to_test] = new_code

            # Update the generated code dictionary
            self.project_generator.add_file(generated_code_dict[class_to_test][0], new_code)
            generated_code_dict[class_to_test] = (
            generated_code_dict[class_to_test][0], new_code, generated_code_dict[class_to_test][2])


    def _regenerate_code_func(self, class_to_test, generated_code_dict, dependencies):
        regeneration_func = lambda reflection_context: self.rc.todo.run(
            self.project,
            self.get_lex_app_context("Lex project"),
            self.extract_relevant_code(class_to_test, generated_code_dict, dependencies),
            {'class': class_to_test, 'path': generated_code_dict[class_to_test][0]},
            self.user_feedback,
            self.get_import_pool(self.project.name, [(class_to_test, generated_code_dict[class_to_test][0])]),
            reflection_context=reflection_context
        )

        return regeneration_func

    async def _act(self):
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

            while not success and attempts < self.max_attempts:
                result = await self.test_executor.execute_test(test_file_name, project_name)
                success = result['success']

                if not success:
                    correct_code_so_far = {}
                    response_json = result.get('response_json')
                    new_code = await self._handle_test_failure(
                        set_to_test,
                        generated_code_dict,
                        test_json,
                        relevant_codes,
                        response_json
                    )
                # Update generated code dictionary with new code
                # ... (rest of the implementation)