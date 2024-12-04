from asgiref.sync import sync_to_async
from lex.lex_ai.metagpt.roles.LLM import LLM
import json
from lex_ai.metagpt.get_files_to_generate import get_files_to_generate
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor


async def generate_model_structure(project_structure, project, user_feedback=""):
    role = LLM()

    example = """
    {
    "Folder1": {
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
      },
        "Folder2": {
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
      },
      "Folder3": {
      "Downloads": {
        "id": "AutoField (Primary Key)",
        "report": "XLSXField",
        ...otherfields
      },
      },
      ...otherfoldersandclasses
    } 
    """

    prompt = f"""
    1. Given a json that has all entities and relationships you will create react json object exactly like given below.
    2. As field types, be careful to use correct names from builtin Django model fields.
    3. Models relationships are mandatory, you should use ForeignKey for relationships.
    4. No ```json
    5. Use double quotes for keys and values
    6. Do not include anything apart from the fields such as descriptions or methods.
    7. Do not write otherFields, instead write every field explicitly.
    8. Only one level folder hierchies are allowed

    Project Structure: 
    {project_structure}

    Example:
    {example}
    
    Current Project Model Structure:
    {"This is the first time for this query, there is no project model structure." if not user_feedback else project.models_fields}
    
    User Feedback:
    {"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

    **Output**:
    Return only the json without ```json:
    json =  
    """

    rsp = await role.run(prompt)

    project.models_fields = json.loads(rsp.content)
    await sync_to_async(project.save)()

    await get_files_to_generate(project)

    await StreamProcessor.global_message_queue.put("DONE")
    return json.loads(rsp.content)