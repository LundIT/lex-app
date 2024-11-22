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

    async def run(self, project, json_to_generate, generated_jsons):
        prompt = generate_test_jsons_prompt(project, json_to_generate, generated_jsons=generated_jsons)
        code = await self._aask(prompt)
        return code