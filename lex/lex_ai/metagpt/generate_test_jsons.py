import yaml

from lex_ai.metagpt.LexContext import LexContext
from lex_ai.metagpt.TestContext import TestContext
from lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from lex_ai.metagpt.roles.LLM import LLM


def generate_test_jsons_prompt(project, json_to_generate):
    example_output = """
    [
  {
    "class": "<ClassName>",
    "action": "create",
    "tag": "classname_<object_pk>",
    "parameters": {
      "date_time_field": "datetime:2023-12-12",
      "text_field": "2024-Q4",
      "foreign_key_field": "tag:classname_<object_pk>",
      "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
      "integer_field": 1,
      "float_field": 1.0,
      "boolean_field": true,
    }
  },
  {
    "class": "<ClassName>",
    "action": "update",
    "tag": "classname_<object_pk>",
    "filter_parameters": {
      "period": "tag:classname_<object_pk>"
    },
    "parameters": {
      "date_time_field": "datetime:2023-12-12",
      "text_field": "2024-Q4",
      "foreign_key_field": "tag:classname_<object_pk>",
      "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
      "integer_field": 1,
      "float_field": 1.0,
      "boolean_field": true,
      "is_calculated": "IN_PROGRESS"
    }
  },
  {
    "class": "ClassName",
    "action": "delete",
    "filter_parameters": {}
  }
]
    """
    prompt: str = f"""
    Lex App Context:
        Key classes and their Required Imports:
            {yaml.dump(LexContext()._prompts)} 

    SPECIFICATIONS:
        Project Overview:
            {project.overview}

        Project Functionalities:
            {project.functionalities}

        Project Models and Fields:
            ```
            {project.models_fields}
            ```
        Project Business Logic Calculations:
            {project.business_logic_calcs}

        Project Structure:
            ```
            {project.detailed_structure}
            ```

        Project Input and Output Files:
            ```
            {project.files_with_analysis}
            ```
    
    Model Code to generate the test json for it:
    {json_to_generate[2]} 

    **Generation requirement**:
    Before starting to generate the test json, please read the following requirements:
        1. Only generate the next test json and then stop generating for the model code and the class name given to you.
        2. While generating test jsons take the example test json into consideration.
        3. Be aware that the test json that you wrote will be used by a test class which is inhereting ProcessAdminTestCase from lex_app
        4. Please create the test json for the cases of the User Story mentioned in the business logic 
        5. Use is_calculated field in the test json object if the class of that object is inhererting from CalculationModel, in our case those models are Report and Upload models
        6. No ```json
        
        
    **Example Test Json**:
    {example_output}

    The next test json to generate is: {json_to_generate[0]}

    Please just regenerate the class and stop according to the test and error code and then stop:

    **Output**:
    Return only the json without ```json:
    
    json =    
    """
    return prompt


async def generate_test_jsons(project):
    from lex_ai.metagpt.roles.JsonGenerator import JsonGenerator
    role = JsonGenerator(project)
    rsp = await role.run("START")

    return rsp.content
