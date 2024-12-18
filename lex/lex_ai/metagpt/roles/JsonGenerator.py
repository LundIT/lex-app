from lex_ai.metagpt.ProjectGenerator import ProjectGenerator
from lex_ai.metagpt.actions.GenerateJson import GenerateJson
from metagpt.schema import Message
from lex_ai.metagpt.generate_test_jsons import generate_test_python_jsons_alg
from lex_ai.metagpt.roles.LexRole import LexRole




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
        test_generate = ProjectGenerator(project_name, self.project, json_type=True)

        redirected_dependencies = self.get_dependencies_redirected(self.generated_code_dict)
        dependencies = self.get_dependencies(self.generated_code_dict)
        test_groups = self.get_models_to_test(redirected_dependencies)

        subprocesses = []

        test_data_path = "Tests"
        test_json_data_path = f"{test_data_path}/test_data"


        # _authentication_settings.py
        test_generate.add_file("_authentication_settings.py", f"initial_data_load = '{project_name}/{test_json_data_path}/test.json'")

        generated_json_dict = {}

        for set_to_test in test_groups:
            set_dependencies = {d for cls in set_to_test for d in redirected_dependencies[cls]}

            combined_class_name = "_".join(set_to_test)

            class_name = combined_class_name + "Test"
            test_file_name = f"test_{class_name}.py"
            test_json_file_name = f"{class_name}.json"

            test_path = f"{test_data_path}/{test_file_name}"
            test_json_path = f"{test_json_data_path}/{test_json_file_name}"

            # Generate test for current class
            relevant_codes = self.extract_relevant_code(set_to_test, self.generated_code_dict, dependencies)

            if len(set_to_test) == 1:
                class_code = self.get_code_from_set(set_to_test, self.generated_code_dict)
                relevant_codes += "\n\n" + class_code
                set_dependencies.add(list(set_to_test)[0])

            relevant_json = self.extract_relevant_json(set_to_test, generated_json_dict, redirected_dependencies)

            test_import_pool = self.get_import_pool(
                project_name,
                [(cls, self.generated_code_dict[cls][0]) for cls in set_dependencies]
            )

            print(f"Generating test json for {class_name}...")

            test_json = await self.rc.todo.run(
                self.project,
                (", ".join(set_to_test), relevant_codes),
                relevant_json
            ) + "\n\n"

            generated_json_dict[combined_class_name] = test_json

            sub_subprocesses = self.get_models_to_test(self.get_relevant_dependency_dict(combined_class_name, redirected_dependencies))
            helper = lambda x: "{\n\t" + f'"subprocess" : "{self.get_test_path(test_json_data_path, x, project_name)}"' + "\n}"
            sub_subprocesses = [helper(subprocess) for subprocess in sub_subprocesses]
            subprocesses.append(helper(combined_class_name))
            content = '[\n' + ',\n'.join(sub_subprocesses) + "\n]"
            start_test_path = f"{test_json_data_path}/test_{combined_class_name}.json"

            test_file = generate_test_python_jsons_alg(
                set_to_test=set_to_test,
                json_path=f"{project_name}/{start_test_path}"
            )

            test_generate.add_file(start_test_path, content)
            test_generate.add_file(test_json_path, test_json)
            test_generate.add_file(test_path, test_file)

        content = '[\n' + ',\n'.join(subprocesses) + "\n]"
        test_generate.add_file(f"{test_json_data_path}/test.json", content)

        return Message(content="Jsons generated successfully", role=self.profile, cause_by=type(self.rc.todo))


