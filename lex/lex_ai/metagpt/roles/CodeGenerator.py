import os

from asgiref.sync import sync_to_async
from django.core.management import call_command

from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex_ai.metagpt.ProjectGenerator import ProjectGenerator
from lex_ai.metagpt.actions.GenerateCode import GenerateCode
from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts

from metagpt.roles.role import Role

from lex.lex_ai.metagpt.generate_test_for_code import generate_test_for_code
from lex.lex_ai.metagpt.run_tests import run_tests, get_failed_test_classes


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

    async def _act(self) -> Message:
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name)
        lex_app_context = self.get_lex_app_context("Lex project")
        all_classes = list(self.project.classes_and_their_paths.items())

        # Generate import pool
        import_pool = "\n".join([
            f"Class {class_name}\n\tImporPath:from {project_name}.{path.replace(os.sep, '.').rstrip('.py')} import {class_name}"
            for class_name, path in all_classes
        ])

        # Step 1: Generate all classes first
        generated_code = ""
        for class_to_generate in all_classes:
            path = class_to_generate[1].replace('\\', '/').strip('/')
            await StreamProcessor.global_message_queue.put(f"code_file_path:{path}\n")

            code = await self.rc.todo.run(
                self.project,
                lex_app_context,
                generated_code,
                class_to_generate,
                self.user_feedback,
                import_pool,
                None
            ) + "\n\n"

            project_generator.add_file(class_to_generate[1], code)
            generated_code += code

        # Apply initial database changes
        await sync_to_async(call_command)("makemigrations")
        await sync_to_async(call_command)("migrate")

        # Step 2: Generate and test each class, regenerating if tests fail
        test_code = ""
        classes_to_fix = []
        max_attempts = 3

        for class_to_test in all_classes:
            attempts = 0
            success = False

            while not success and attempts < max_attempts:
                # Generate test for current class
                test = await generate_test_for_code(
                    generated_code,
                    self.project,
                    import_pool,
                    class_to_test,
                    test_code
                )

                # Add test file
                test_file_name = f"test_{class_to_test[0]}Test.py"
                project_generator.add_file(f"Tests/{test_file_name}", test)

                # Run the test
                response_data = await sync_to_async(run_tests)(project_name, test_file=test_file_name)
                print(response_data)
                success = response_data.get("success")

                if not success:
                    # If test failed, regenerate the class
                    stderr_info = {
                        'test_code': test,
                        'class_code': generated_code,
                        'error_message': response_data.get("console_output", {}).get("stderr", [])
                    }

                    # Regenerate the failed class
                    new_code = await self.rc.todo.run(
                        self.project,
                        lex_app_context,
                        generated_code,
                        class_to_test,
                        self.user_feedback,
                        import_pool,
                        stderr_info
                    ) + "\n\n"

                    # Update the generated code
                    old_code = generated_code
                    generated_code = generated_code.replace(
                        [c for c in generated_code.split("### ") if class_to_test[0] in c][0],
                        new_code.split("### ")[-1]
                    )

                    project_generator.add_file(class_to_test[1], new_code)

                    # Reapply migrations if needed
                    # call_command("makemigrations")
                    # call_command("migrate")

                    attempts += 1
                else:
                    test_code += test
                    break

            if not success:
                classes_to_fix.append(class_to_test)

        # Return results
        message = Message(
            content=generated_code,
            role=self.profile,
            cause_by=type(self.rc.todo),
            metadata={
                'failed_classes': classes_to_fix,
                'test_code': test_code
            }
        )
        return message
    def get_lex_app_context(self, prompt):
        rag = RAG()
        i, j = rag.memorize_dir(RAG.LEX_APP_DIR)

        # lex_app_context = "\n".join([rag.query_code("LexModel", i, j, top_k=1)[0],
        #                              rag.query_code("CalculationModel", i, j, top_k=1)[0],
        #                              rag.query_code("LexLogger", i, j, top_k=1)[0],
        #                              rag.query_code("XLSXField", i, j, top_k=1)[0]])
        lex_app_context = "\n".join(rag.query_code("LexModel, CalculationModel, XLSXField, LexLogger", i, j, top_k=30))


        return lex_app_context
