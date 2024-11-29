import asyncio
import re

from asgiref.sync import async_to_sync
from lex_ai.metagpt.generate_project_code import generate_project_code_prompt_old, regenerate_project_code_prompt
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message


from lex.lex_ai.metagpt.generate_test_jsons import generate_test_jsons_prompt


class GenerateJson(Action):
    name: str = "GenerateJson"

    async def run(self, project, json_to_generate, generated_jsons, number_of_objects_for_report):
        prompt = generate_test_jsons_prompt(project, json_to_generate, generated_jsons=generated_jsons, number_of_objects_for_report=number_of_objects_for_report)
        code = await self._aask(prompt)
        return code

class GenerateJsonRole(Role):
    name: str = "GenerateJsonRole"
    profile: str = "Expert in generating test jsons"

    def __init__(self, project, json_to_generate, generated_json, number_of_objects_for_report, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateJson])
        self.project = project
        self.json_to_generate = json_to_generate
        self.generated_jsons = generated_json
        self.number_of_objects_for_report = number_of_objects_for_report


    async def _act(self) -> Message:
        project = self.project
        generated_jsons = self.generated_jsons
        json_to_generate = self.json_to_generate
        number_of_objects_for_report = self.number_of_objects_for_report

        generated_json = await self.rc.todo.run(project, json_to_generate, generated_jsons, number_of_objects_for_report)
        return Message(content=generated_json, role_profile=self.profile)