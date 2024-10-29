import json

from asgiref.sync import sync_to_async

from lex_ai.metagpt.roles.LLM import LLM


async def get_files_to_generate(project):
    role = LLM()

    example = """
    {
        "class_name1": "path/to/class1.py",
        "class_name2": "path2/to2/class2.py",
        ...
    } 
    """
    prompt = f"""
    old structure: 
    {project.structure}

    Example:
    {example} 
    
    updated models and their names:
    {project.models_fields}

    1. Give back a json that holds the files structure of the new models and their fields, according to the old file structure and the example.
    2. Don't include anything else just classname as key and path as value.
    3. replace the 'path/to/' with the path from the model_fields and old structure, find the class path and replace it
    
    **Output**:
    Return only the json without ```json:
    json =  
    """

    rsp = (await role.run(prompt)).content

    project.classes_and_their_paths = json.loads(rsp)
    await sync_to_async(project.save)()
    return json.loads(rsp)
    
    