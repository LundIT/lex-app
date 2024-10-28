import asyncio
import os
import re

from asgiref.sync import async_to_sync, sync_to_async
from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.roles.di.data_interpreter import DataInterpreter
import json
import json5
from lex.lex_ai.metagpt.roles.LLM import LLM

from lex.lex_ai.rag.rag import RAG
from metagpt.schema import Message
from lex.lex_ai.utils import global_message_queue


async def generate_project_structure(project_overview, files_with_explanations, project, user_feedback=""):
    # team = Team()
    #
    # team.hire([
    #     DataInterpreter(max_react_loop=1, tools=["<all>"], react_mode="react", code_result=True),
    #     LLM()
    # ])

    role = LLM()
    code_role = LLM()
    json_role = LLM()

    prompt = """
        Given the project overview and the files with explanations:

        [START INSTRUCTIONS]
        1. Use project overview and files provided as a requirement specification used for doing object design drafts
        2. Represent relationships of the entity classes that works according to the project description and files with explanations
        4. Input files are the entity classes that should be modeled (this is the models classes, it should be **Extracted from the project description and explanations and file content, think of models that makes sense**)
        5. The models that handles the uploads of corresponding entity classes resides in the Upload Files Folder (It has the name `Classname`Upload)
        6. For every input model there should be a corresponding model class in Upload Files folder that handles it's upload mechanism and also it's processing 
            example: class1 is in Input then UploadClass1 is in Upload Files
        7. Represent the file structure also in the json. (where the entity classes will reside)
        8. You will seperate between Inputs and Reports and Uploads files, in Reports there is only "Download" class that has the logic which lets create a "Output" Report like in the files sepciefied where you can download it
        9. Only names from project description/explanations but in software engineering conventions (No file names, no underscore, a little bit abstract)
        10. Use capitalcase naming for the entity classes
        11. choose field that makes sense according to the files content
        12. add detailed describtion for each class
        13. **The json should parsable, make it simple**
        14. Database schema should be normalized, so craete entiteis in a way that they are normalized
        14. **No ```json**
        [END INSTRUCTIONS]

        Input:
            Model Classes
        Upload Files:
            Model that handles the input of the input classes 
        Reports:
            Only one class called Download which is used for download the processed report


        Context:
        Project Overview:
        {project_overview}

        Files with Explanations:
        {file_context}


        **Outputs**:
        => Only return a json object encapsulating the **Requirements** above, no ```json
        json = 

        """
    prompt = """
        Given the project overview and the files with explanations:

        [START INSTRUCTIONS]
        1. Use project overview and files provided as a requirement specification used for doing object design drafts
        2. Represent relationships of the entity classes that works according to the project description and files with explanations
        4. Input files are the entity classes that holds the data and should be modeled (this is the models classes, it should be **Extracted from the project description and explanations and file content, think of models that makes sense**)
        5. Introduce models that handles the upload of the corresponding entity classes when providing data (make it work with the data provided in the files)
        6. Represent the file structure also in the json. (where the entity classes will reside)
        8. You will seperate between models and models that upload the models, and also the Reports (Decide on a structure that makes sense).
        9. For reports try to get inspiration for the files provided (Output/Report files) define some kind of a model or logic that generates the report from all the input models
        10. Only names from project description/explanations but in software engineering conventions (No file names, no underscore, a little bit abstract)
        11. Use capitalcase naming for the entity classes
        12. choose field that makes sense according to the files content
        13. add detailed describtion for each class
        14. **The json should parsable, make it simple**
        15. Database schema should be normalized, so craete entiteis in a way that they are normalized
        15. **No ```json**
        [END INSTRUCTIONS]

        Context:
        Project Overview:
        {project_overview}

        Files with Explanations:
        {file_context}
        
        User Feedback: 
        {user_feedback}

        **Outputs**:
        => Only return a json object encapsulating the **Requirements** above, no ```json
        json = 

        """

    output_code = """
        Use LexModels models for creating the entity classes and `CalculationModel` for the ones who needs processing.
        The ones that needs processing uses CalculationModel and overrides the def calculate() function available from CalculationModel.

        1. For the specified classes with the correct structure.
        2. give calculations that makes sense
        3. datasamples are just examples, create code that would work for anything
        4. use conventional names for entities (class like)
        5. Use a **LexLogger** for the logging
        6. Write the corresponding fields using lex_app or django fields
        7. Extend CalculationModel class (for Processing), Extend LexModel for normal entities
        8. Document and log everything

        lex_app context:
        {lex_app_context} 

        File with Explanations:
        {file_context}


        Project Structure (Entity and relationships) this is to be implemented:
        {project_structure}

        **Outputs**:
        => Only return code no ```python

        code: 
        """

    transform_prompt = """
        Transform the json given to the same structure as the given json format:
        1. Don't include project details and overview, only include files and folders, classes and explanations.

        Given Json:
        {given_json}

        Specified Format:
        {specified_json}


        **Outputs**:
            output only the json without ```json:

        json =  
        """

    specified_json = """
        {
          "Folder1": {
            "class1": "Explanation 1"
            "class2": "Explanation 2"
          },
          "Folder2": {
            "class3": "Explanation 3"
            "class4": "Explanation 4"
          }
        } 
        """

    # components = [
    #     {
    #         'name': file['name'],
    #         'type': 'File',
    #         'explanation': file['explanation']
    #     } for file in files_with_explanations
    # ]
    # project_structure = {
    #     'project_name': project_overview['name'],
    #     'project_description': project_overview['description'],
    #     'project_type': project_overview['type'],
    #     'components': components
    # }
    #

    rsp = await enrich_json_with_files_content(files_with_explanations)

    rsp_json = await role.run(prompt.format(project_overview=json.dumps(project_overview),
                                            file_context=rsp,
                                            user_feedback="This is the first time for this query, there is no user feedback." if not user_feedback
                                            else user_feedback))

    rsp_json = rsp_json.content

    rsp_specified_json = await json_role.run(transform_prompt.format(given_json=rsp_json, specified_json=specified_json))

    rsp_specified_json = rsp_specified_json.content

    rag = RAG()
    i, j = rag.memorize_dir(os.getenv("METAGPT_PROJECT_ROOT"))
    lex_app_context = rag.query_code("LexModel, CalculationModel, XLSXField, LexLogger", i, j, top_k=10)

    # rsp_code = (async_to_sync(code_role.run)
    #             (output_code.format(project_structure=rsp_json, file_context=rsp,
    #                                 lex_app_context=lex_app_context)).content)
    project.structure = json.loads(rsp_specified_json)
    project.detailed_structure = json.loads(rsp_json)
    project.files_with_analysis = rsp

    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    print("[START FINAL]\n", rsp_json, "\n[END FINAL]")
    return json.loads(rsp_json), json.loads(rsp_specified_json), rsp


async def enrich_json_with_files_content(files_with_explanations):
    role = DataInterpreter(max_react_loop=1, tools=["<all>"], react_mode="react", code_result=True)

    prompt = f"""
    Given the files with explanations, analyze the content of the files and understand the components of the project and their relationships. 
    [START INSTRUCTIONS]
    1. Open the file and get the content
    1. Transform the every Timestamp to the form or format of YYYY-MM-DD HH:MM:SS or None
    2. Timestamp should be parsable from a json prespective
    3. Name should be without file extensions
    4. no ```json
    5. output of the json should be similar to the `style` defined afterwards
    6. The json should have no whitespaces
    7. Don't model classes from the lex_app, only model the entities from the project description and files content
    [STOP INSTRUCTIONS]

    Files:
    {files_with_explanations} 
    """

    style = """
    **OUTPUT**:
    {
        "components": [
            {
                "name": "",
                "type": "",
                "explanation": "",
                "columns": [
                ],
                "data_sample": [
                    {
                    },
                    {
                    },
                ]
            }
        ]
    }

    result:
    """
    rsp = (await role.run(prompt + style)).content
    print("[START INTERPRETER]\n", files_with_explanations, "\n[END]")
    return rsp