import asyncio
import re

from asgiref.sync import async_to_sync
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json
import json5

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message

class AskLLM(Action):
    name: str = "AskLLLM"
    profile: str = "Ask LLLM for the result of the DataInterpreter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, question: str) -> str:
        rsp = await self._aask(question)
        return rsp
