from asgiref.sync import sync_to_async
from metagpt.roles.di.data_interpreter import DataInterpreter
import json
from lex.lex_ai.metagpt.roles.LLM import LLM

from lex.lex_ai.rag.rag import RAG
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor


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
    better_prompt_new = """
   Given the project overview and the files with explanations:

[START INSTRUCTIONS]

1. Use the project overview and files provided as a requirements specification for drafting an object design.
2. Identify and represent relationships between entity classes based on the project description and file content, treating each input file as a potential entity model.
3. **Incorporate Foreign Key relationships** wherever logical dependencies exist between classes. Analyze each entity to identify connections between them, and create Foreign Key fields to represent these relationships, ensuring a normalized database schema.
4. Treat input files as sources for entity classes, which hold data and should be structured as models. **Extract these models and their relationships based on the project description, file content, and explanations.**
5. In every upload model, there must be a mandatory file field, and in every report model, there must be an OPTIONAL file field.
6. Create models to handle data uploads for each corresponding entity class. Ensure that these upload models can process data according to the columns and types found in the input files.
7. **Analyze the columns in each input file. Create a unique input model for each file that has a unique set of columns. Only if multiple files have an identical set of columns should they be grouped into a shared model.**
8. Represent the file structure in JSON format to indicate where each entity class will reside in the project directory.
9. Separate models logically into main models, upload models, and report models to reflect the structure and purpose of each class.
10. For report models, draw inspiration from the output files and define models or logic that consolidate data from input models to generate reports.
11. **Translate any non-English terms to English** for all model and field names. Use standardized software engineering conventions for names, ensuring consistency.
12. Use capital case for Model and Folder names (e.g., `ModelClass`, `Folder1`) and camel case for field names (e.g., `fieldName`).
13. Choose fields based on file content, and ensure all model names and field names are in English.
14. Provide descriptions for each class to clarify its purpose.
15. Return a simple, parsable JSON object.
16. Normalize the database schema by minimizing redundancy and using Foreign Key relationships wherever logical dependencies exist between classes.
17. Examine the columns and data in each file context to inform model structures, **ensuring a distinct input model for each unique set of columns, grouping only identical structures in shared models**.
18. Ensure report models can use data from input models to generate consolidated reports.
19. **Return only the JSON object that encapsulates these requirements.**
20. Exclude ```json tags; write the JSON object directly.

[END INSTRUCTIONS]

Context:

Project Overview:
{project_overview}

Files with Explanations:
{file_context}

User Feedback:
{user_feedback} 
    """
    better_prompt = """
# Objective:
Process the **Project Overview**, **Files with Explanations**, and **User Feedback** to extract and model the entity classes, their relationships, upload models, and report models. Ensure that the JSON output accurately reflects normalized database schemas and adheres to software engineering conventions.

## Requirements:
1. **Entity Models Extraction**:
   - Extract entity classes from the project description and file contents.
   - Represent relationships between entity classes (e.g., one-to-many, many-to-many).

2. **Upload Models**:
   - Create separate models to handle the upload of each corresponding entity class.
   - Ensure compatibility with the data provided in the files.
   - Has a mandatory file field for data upload.

3. **Report Models**:
   - Define models or logic that can generate reports based on the input models.
   - Derive inspiration from the provided output/report files.
   - Has optional file field for the report file.

4. **File Structure Representation**:
   - Clearly separate **Models**, **UploadModels**, and **Reports**.
   - Use capital case naming for entity classes following software engineering conventions.
   - Ensure that the JSON structure is simple and parsable.

5. **Normalization**:
   - Design the database schema to be normalized.
   - Create distinct entities for input files with differing column structures.

6. **Detailed Descriptions**:
   - Provide comprehensive descriptions for each class and field based on the file contents.

## JSON Structure Guidelines:
- **Main Sections**:
  - `ProjectOverview`
  - `FileStructure`
    - `Models`
    - `UploadModels`
    - `Reports`

- **Classes**:
  - `name`: CapitalCase
  - `description`: Detailed explanation of the class.
  - `fields`: List of fields with `name`, `type`, and `unit` (if applicable).
  - `relationships`: List of relationships with other classes.
  - `constraints`: Any constraints or dependencies.

- **Constraints**:
  - Do not include ```json blocks.
  - Use simple, parsable JSON without unnecessary complexity.
  - Avoid including URLs, links, or bibliographies.
  - Ensure no repetition of copyrighted content.

## Formatting:
- **Headers and Structure**:
  - Use double new lines to separate sections.
  
- **Lists**:
  - Use unordered lists for fields.

- **Code and Math**:
  - Use markdown code blocks with appropriate language tags if necessary.

- **Style**:
  - Use bold sparingly for emphasis.
  - Maintain clear visual hierarchy with appropriate markdown styling.

## Final Output:
Return only a JSON object encapsulating the requirements above. Ensure it is properly formatted and parsable.

**Do not include any additional text, explanations, or markdown formatting outside the JSON object.**

# CONTEXT:
Project Overview:
{project_overview}

Files with Explanations:
{file_context}

User Feedback: 
{user_feedback}

# OUTPUT:
    """

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
        15. check the column information for every input file and model from the **file context** column section
        16. For every input file which has different list of columns from other input files, a seperate input model should be created
        17. The report models should be created in a way that they can be used to generate the report from the input models
        18. **No ```json**
        
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
    melih_prompt = """
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
        16. check the column information for every input file and model from the **file context** column section
        17. For every input file which has different list of columns from other input files, a seperate input model should be created
        18. The report models should be created in a way that they can be used to generate the report from the input models
        19. **No ```json**
        
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

    rsp_json = await role.run(better_prompt_new.format(project_overview=json.dumps(project_overview),
                                            file_context=rsp,
                                            user_feedback="This is the first time for this query, there is no user feedback." if not user_feedback
                                            else user_feedback))

    rsp_json = rsp_json.content

    rsp_specified_json = await json_role.run(transform_prompt.format(given_json=rsp_json, specified_json=specified_json))

    rsp_specified_json = rsp_specified_json.content

    # rag = RAG()
    # i, j = rag.memorize_dir(RAG.LEX_APP_DIR)
    # lex_app_context = rag.query_code("LexModel", i, j, top_k=2)

    # rsp_code = (async_to_sync(code_role.run)
    #             (output_code.format(project_structure=rsp_json, file_context=rsp,
    #                                 lex_app_context=lex_app_context)).content)
    project.structure = json.loads(rsp_specified_json)
    project.detailed_structure = json.loads(rsp_json)
    project.files_with_analysis = rsp

    await sync_to_async(project.save)()
    await StreamProcessor.global_message_queue.put("DONE")
    return json.loads(rsp_json), json.loads(rsp_specified_json), rsp


async def enrich_json_with_files_content(files_with_explanations):
    role = DataInterpreter(max_react_loop=1, tools=["<all>"], react_mode="react", code_result=True)

    prompt = f"""
    
    Files:
    {files_with_explanations}
    
    Given the files with explanations, analyze the content of the files and understand the components of the project and their relationships. 
    [START INSTRUCTIONS]
    1. Open the file and get the content
    2. Transform the every Timestamp to the form or format of YYYY-MM-DD HH:MM:SS or None
    3. Timestamp should be parsable from a json prespective
    4. Name should be without file extensions
    6. output of the json should be similar to the `style` defined above but without whitespaces
    7. The json should have no whitespaces
    8. Output no whitespace or any null bytes, only the json with no ''' json
    9. The json output is kind of large, somtimes the output would be cut off, so do something about that
    [STOP INSTRUCTIONS]
    
    [START OUTPUTING JSON] 
    """

    style = """
    style:
    {
        "components": [
            {
                "name": "",
                "type": "",
                "explanation": "",
                "path": "",
                "columns": [
                ],
                "data_samples": [
                    {
                    },
                    {
                    },
                    {
                    },
                ],
                row_count: 0
            }
        ]
    }
    """


    rsp = (await role.run(style + prompt)).content
    return rsp