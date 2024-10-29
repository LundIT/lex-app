import os

from lex_ai.metagpt.ProjectGenerator import ProjectGenerator
from lex_ai.metagpt.actions.GenerateCode import GenerateCode

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts

from metagpt.roles.role import Role
class CodeGenerator(Role):
    name: str = "CodeGenerator"
    profile: str = "Expert in generating code based on architecture and specifications"

    def __init__(self, project, user_feedback, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateCode])
        self.project = project
        self.user_feedback = user_feedback


    async def _act(self) -> Message:
        print("-----------------------------------------------------------------------------------------------------")
        print("------------------------------------Code Generator---------------------------------------------------")
        project_name = "DemoWindparkConsolidation"
        project_generator = ProjectGenerator(project_name)


        lex_app_context = self.get_lex_app_context("Lex project")
        classes_to_generate = self.project.classes_and_their_paths.items()

        import_pool = "\n".join([f"Class {class_name}\n\tImporPath:from {project_name}.{path.replace(os.sep, '.').rstrip('.py')} import {class_name}" for class_name, path in classes_to_generate])

        generated_code = ""
        for class_to_generate in classes_to_generate:
            code = await self.rc.todo.run(self.project, lex_app_context,
                                                     generated_code, class_to_generate, self.user_feedback, import_pool) + "\n\n"

            print("Classes to generate: ", class_to_generate)
            project_generator.add_file(class_to_generate[1], code)
            generated_code += code



        # python_codes = parse_codes_with_filenames(generated_code)
        #
        # # Outputting the results
        # for file_name, code in python_codes.items():
        #     # Create a Path object
        #     file_path = Path(f"generated_files/{self.context.kwargs.get('timestamp')}/" + file_name)
        #
        #     # Create parent directories if they don't exist
        #     file_path.parent.mkdir(parents=True, exist_ok=True)
        #
        #     # Write to the file
        #     file_path.write_text(code)

        message = Message(content=generated_code, role=self.profile, cause_by=type(self.rc.todo))
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
