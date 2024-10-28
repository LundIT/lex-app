import asyncio
import re

from asgiref.sync import async_to_sync, sync_to_async
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json
from lex.lex_ai.metagpt.roles.LLM import LLM

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.utils import global_message_queue


async def generate_project_functionalities(project_structure, files_with_explanations, project, user_feedback=""):
    role = LLM()

    prompt = f"""
    File content and their explanations:
    {files_with_explanations} 

    Project Structure:
    {project_structure} 
    
    Current Project Functionalities:
    {"This is the first time for this query, there is no project functionality." if not user_feedback else project.functionalities}
    
    User Feedback:
    {"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

    [START INSTRUCTIONS]
    1.Given the project structure, summarize the main functionalities of the project.
    2.Should be returned in a markdown format.
    3. No ```.
    [STOP INSTRUCTIONS]

    start of markdown:
    """

    rsp = (await role.run(prompt)).content
    project.functionalities = rsp
    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    return rsp