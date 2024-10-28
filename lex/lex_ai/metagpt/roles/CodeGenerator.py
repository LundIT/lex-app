import asyncio
import re

from asgiref.sync import async_to_sync
from lex_ai.metagpt.actions.GenerateCode import GenerateCode
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts

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
        lex_app_context = self.get_lex_app_context("Lex project")
        classes_to_generate = [f[0] for f  in self.project.models_fields.items()]

        generated_code = ""
        for class_to_generate in classes_to_generate:
            generated_code += await self.rc.todo.run(self.project, lex_app_context,
                                                     generated_code, class_to_generate, self.user_feedback) + "\n"


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
        index, source_code_chunks = rag.memorize_dir(os.getenv("METAGPT_PROJECT_ROOT"))
        relevant_chunks = rag.query_code(LexPrompts.PROMPT_REQUIREMENT, index, source_code_chunks, top_k=40)
        return "\n".join(relevant_chunks)
