import asyncio
import re

from asgiref.sync import async_to_sync
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message

class AskLLM(Action):
    name: str = "AskLLLM"
    profile: str = "Ask LLLM for the result of the DataInterpreter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, question: str, system="") -> str:
        if system:
            rsp = await self._aask(question, [system])
        else:
            rsp = await self._aask(question)
        return rsp
