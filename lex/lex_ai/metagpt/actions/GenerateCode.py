import asyncio
import re

from asgiref.sync import async_to_sync
from lex_ai.metagpt.generate_project_code import generate_project_code_prompt
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json
import json5

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message

class GenerateCode(Action):
    name: str = "GenerateCode"

    async def run(self, project, lex_app_context: str, code: str, class_to_generate: str, user_feedback):
        prompt = generate_project_code_prompt(project, lex_app_context, code, class_to_generate, user_feedback)

        code = await self._aask(prompt, [
            "** [YOU ARE A SOFTWARE ENGINEER AND YOU ARE TASKED TO COMPLETE EVERYTHING IN THE PROJECT] **"
        ])

        return code