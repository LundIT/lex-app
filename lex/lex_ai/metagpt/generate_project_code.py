from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts
import asyncio
import re

from asgiref.sync import sync_to_async
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
from lex.lex_ai.metagpt.roles.LLM import LLM
import json
import json5

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.utils import global_message_queue

def generate_project_code_prompt(project, lex_app_context, code, class_to_generate):
    prompt: str = f"""
    
    Lex App Context:
    {lex_app_context}
    
    SPECIFICATIONS:
    
    Project Overview:
    {project.overview}
    
    Project Input and Output Files:
    {project.files_with_analysis}
    
    Project Structure:
    {project.detailed_structure}
    
    Project Functionalities:
    {project.functionalities}
    
    Project Models and Fields:
    {project.models_fields}
    
    Project Business Logic Calculations:
    {project.business_logic_calcs}
    
    Project Requirement: 
    {LexPrompts.PROMPT_REQUIREMENT}
    
    # **Available code:**
        {code}
       
           
    Generation requirement. Before starting to generate the code, please read the following requirements:
    1. Only generate the next class and then stop generating.
    2. No class Meta is allowed
    3. Don't use self.is_calculated
    4. Use imports ProjectName.<class_name> or ProjectName.<function_name>
    5. Implement everything method
    6. Use python convention for class names
    
    The next class to generate is: {class_to_generate}
    
    """

    return prompt


async def generate_project_code(project, user_feedback=""):
    from lex_ai.metagpt.roles.CodeGenerator import CodeGenerator
    role = CodeGenerator(project)

    rsp = await role.run("START")

    project.generated_code = rsp.content
    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    return rsp.content