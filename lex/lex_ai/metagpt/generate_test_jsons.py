import yaml

from lex_ai.metagpt.LexContext import LexContext
from lex_ai.metagpt.TestContext import TestContext
from lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from lex_ai.metagpt.roles.LLM import LLM


def generate_test_jsons_prompt(project, json_to_generate, generated_jsons):
    example_output = """
    [
  {
    "class": "<ClassName>",
    "action": "create",
    "tag": "class_name_<object_pk>",
    "parameters": {
      "date_time_field": "datetime:2023-12-12",
      "text_field": "2024-Q4",
      "foreign_key_field": "tag:class_name_<object_pk>",
      "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
      "integer_field": 1,
      "float_field": 1.0,
      "boolean_field": true,
    }
  },
  {
    "class": "<ClassName>",
    "action": "update",
    "tag": "class_name_<object_pk>",
    "filter_parameters": {
      "period": "tag:class_name_<object_pk>"
    },
    "parameters": {
      "date_time_field": "datetime:2023-12-12",
      "text_field": "2024-Q4",
      "foreign_key_field": "tag:class_name_<object_pk>",
      "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
      "integer_field": 1,
      "float_field": 1.0,
      "boolean_field": true,
      "is_calculated": "IN_PROGRESS"
    }
  }
]
    """
    
    
    
    example = """
     {
        "class": "<ClassUpload>",
        "action": "create",
        "tag": "<class>_upload_<object_pk>",
        "parameters": {
          "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
          "is_calculated": "IN_PROGRESS"
        }
    }
  
    The above test creates <Class> objects by using <ClassUpload> and below test should use <Class> instead of <ClassUpload> because in the actual logic it is actually depending on <Class> objects and not <ClassUpload> objects: 
     {
        "class": "<Class2Upload>",
        "action": "create",
        "tag": "<class2>_upload_<object_pk>",
        "parameters": {
          "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
          "is_calculated": "IN_PROGRESS",
          "<class>_id": "<object_pk>"
        }
    }
    As you may realized, I uesd "<class>_id": "<object_pk>" line to define foreign key relationship between <Class> and <Class2Upload> objects.
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
    {json_to_generate[1]} 


    Already Generated Test Jsons (Test were executed and the data is already available in the database, please reuse the data for the next json test):
    {generated_jsons}
    
    **Generation requirement**:
    Before starting to generate the test json, please read the following requirements:
        1. Only generate the next test json and then stop generating for the model code and the classes name given to you.
        2. While generating test jsons take the example test json into consideration.
        3. Be aware that the test json that you wrote will be used by a test class which is inhereting ProcessAdminTestCase from lex_app
        4. Please create the test json for the cases of the User Story mentioned in the business logic 
        5. Do not use any upload model as a foreign key in the test json object, instead use their corresponding input model as a foreign key (e.g. use <Class> instead of <Class>Upload: "<class>_id" : "<object_pk>"):
        Example: {example} 
        
        6. Use is_calculated field in the test json object if the class of that object is inhererting from CalculationModel, in our case those models are Report and Upload models
        7. When you upload a file with a create test by assigning is_calculated to IN_PROGRESS, There is no need for an extra update test for that calculation which is being triggered by the file upload
        8. Build upon the test jsons that were already provided to you 
        9. No delete test cases
        10. Please no ```json
        
        
    **Example Test Json**:
    {example_output}

    The next test json to generate is: {json_to_generate[0]}

    Please just regenerate the classes mentioned and stop according to the test and error code and then stop:

    **Output**:
    Return only the json without ```json:
    
    json =    
    """
    return prompt

async def generate_test_python_jsons(project, test_to_generate, json_path):
    role = LLM()
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

       Model Code to generate the test for it:
       {test_to_generate[1]} 

       **Generation requirement**:
       Before starting to generate the ProcessAdminTestCase python test, please read the following requirements:
           1. Only generate the next test and then stop generating for the model code and the class name given to you.
           2. While generating tests take the example test json into consideration.
           3. Be aware that the test json that you wrote will be used by a test class which is inhereting ProcessAdminTestCase from lex_app
           4. Please create the test for the cases of the User Story mentioned in the business logic 
           5. No ```python
       **Example Test**:

       The next test to generate is: {",".join(test_to_generate[0])}

       Please just regenerate the class and stop according to the test and error code and then stop:
       
     Test Structure:
     ```python
     from lex.lex_app.tests.ProcessAdminTestCase import ProcessAdminTestCase

     class {"".join(test_to_generate[0])}Test(ProcessAdminTestCase):
         test_data = "{json_path}"
         
         # Leave it empty like this
         def test(self):
             pass  

     ``` 

       **Output**:
         Return only the python test code without ```python and ```:

       code:
           
       """
    rsp = (await role.run(prompt)).content

    return rsp

def generate_test_python_jsons_alg(set_to_test, json_path):
    return f"""
from django.core.management import call_command
from lex.lex_app.tests.ProcessAdminTestCase import ProcessAdminTestCase
from lex_app import settings

class {"".join(set_to_test)}Test(ProcessAdminTestCase):
    test_path = "{json_path}"
       
    def tearDown(self):
        call_command('flush', verbosity=0, interactive=False)  
        
    def test(self):
        pass   
    """ 



async def generate_test_jsons(project):
    from lex_ai.metagpt.roles.JsonGenerator import JsonGenerator
    role = JsonGenerator(project)
    rsp = await role.run("START")

    return rsp.content
