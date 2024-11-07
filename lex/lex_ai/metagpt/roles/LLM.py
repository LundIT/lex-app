import asyncio
import re

from asgiref.sync import async_to_sync
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
from lex.lex_ai.metagpt.actions.AskLLM import AskLLM
import json

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message

class LLM(Role):
    name: str = "LLM"
    profile: str = "Gets the result of the LLM output"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system = kwargs.get('system', "")
        self.set_actions([AskLLM])

    async def _act(self) -> Message:
        message = self.get_memories()[0].content
        self.get_memories().clear()
        result = await self.todo.run(message, self.system)
        return Message(content=result, role=self.name, role_profile=self.profile)