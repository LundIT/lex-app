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

async def generate_model_structure(project_structure, project, user_feedback=""):
    role = LLM()

    example = """
    {
      "Class1": {
        "id": "AutoField (Primary Key)",
        "class_to_another_class": "ForeignKey (to self)",
        "name": "TextField",
        "date": "DateTimeField",
        ...otherfields
      },
      "Class2": {
        "id": "AutoField (Primary Key)",
        "period": "ForeignKey (to Period)",
        "class2": "TextField",
        "number_of_class5": "IntegerField",
        "year": "IntegerField",
        "investment": "FloatField",
        "employees": "IntegerField",
        "area": "FloatField",
        ...otherfields
      },
      "report_cashflow_expample": {
        "id": "AutoField (Primary Key)",
        "upload_id": "IntegerField",
        "class_4": "ForeignKey (to Class4)",
        "class1_name": "ForeignKey (to Class1)",
        "date": "DateTimeField",
        "year": "IntegerField",
        "cashflow": "FloatField",
        ...otherfields
      },
      "Downloads": {
        "id": "AutoField (Primary Key)",
        "report": "XLSXField",
        ...otherfields
      },
      ...otherclasses
    } 
    """

    prompt = f"""
    1. Given a json that has all entities and relationships you will create react json object exactly like given below.
    2. As field types, be careful to use correct names from builtin Django model fields.
    3. No ```json
    4. Use double quotes for keys and values
    5. Do not include anything apart from the fields such as descriptions or methods.
    6. Do not write otherFields, instead write every field explicitly.

    real json: 
    {project_structure}

    Example:
    {example}
    
    Current Project Structure:
    {"This is the first time for this query, there is no project structure." if not user_feedback else project.models_fields}
    
    User Feedback:
    {"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

    **Output**:
    Return only the json without ```json:
    json =  
    """

    rsp = await role.run(prompt)

    project.models_fields = json.loads(rsp.content)
    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    return json.loads(rsp.content)