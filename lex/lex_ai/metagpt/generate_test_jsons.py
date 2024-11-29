import yaml

from lex_ai.metagpt.LexContext import LexContext
from lex_ai.metagpt.TestContext import TestContext
from lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from lex_ai.metagpt.roles.LLM import LLM


def generate_test_jsons_prompt(project, json_to_generate, generated_jsons, number_of_objects_for_report=None):

    report_context = f"""""" if number_of_objects_for_report is None else f"""Number of objects for the report dependency (From the database): {number_of_objects_for_report}"""
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
        "type": "Upload",
        "input_tag": "<class>" // (always lowercase and seperated by "_") Since the <ClassUpload> is the Upload class of the <Class> model, we need to define the input tag to be able to use the <Class> object in the next tests
        "parameters": {
          "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
          "is_calculated": "IN_PROGRESS",
        }
    }
  
    The above test creates <Class> objects by using <ClassUpload> and below test should use <Class> instead of <ClassUpload> because in the actual logic it is actually depending on <Class> objects and not <ClassUpload> objects: 
     {
        "class": "<Class2Upload>",
        "action": "create",
        "tag": "<class2>_upload_<object_id>", // object_id is an int
        "type": "Upload",
        "input_tag": "<class2>" //(always lowercase and seperated by "_") Since the <Class2Upload> is the Upload class of the <Class2> model, we need to define the input tag to be able to use the <Class2> object in the next tests
        "parameters": {
          "file_field": "<ProjectName>/Tests/input_files/<file_name>.xlsx",
          "is_calculated": "IN_PROGRESS",
        },
    }
    
    Report Example (Knowing that there is 4 objects of ExampleDependency in the database):
[
  {
    "class": "ExampleReport",
    "action": "create",
    "tag": "example_report_1",
    "type": "Report",
    "parameters": {
      "sum": 0.0,
      "exampleDependency": "example_dependency_1", // Never use upload models here
      "file": "<ProjectName>/<Folder>/../<OutputName>_1.xlsx",
      "is_calculated": "IN_PROGRESS"
    }
  },
  },
  {
    "class": "ExampleReport",
    "action": "create",
    "tag": "example_report_2",
    "type": "Report",
    "parameters": {
      "sum": 0.0,
      "exampleDependency": "example_dependency_2", // Never use upload models here
      "file": "<ProjectName>/<Folder>/../<OutputName>_2.xlsx",
      "is_calculated": "IN_PROGRESS"
    }
  },
    {
    "class": "ExampleReport",
    "action": "create",
    "tag": "example_report_3",
    "type": "Report",
    "parameters": {
      "sum": 0.0,
      "exampleDependency": "example_dependency_3", // Never use upload models here
      "file": "<ProjectName>/<Folder>/../<OutputName>_3.xlsx",
      "is_calculated": "IN_PROGRESS"
    }
  },
    {
    "class": "ExampleReport",
    "action": "create",
    "tag": "example_report_4",
    "type": "Report",
    "parameters": {
      "sum": 0.0,
      "exampleDependency": "example_dependency_4", // Never use upload models here
      "file": "<ProjectName>/<Folder>/../<OutputName>_4.xlsx",
      "is_calculated": "IN_PROGRESS"
    }
  },
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
            Example for class <Class>:
             class <ClassUpload>(CalculationModel):
                file_field = models.FileField(upload_to='Tests/input_files/')
                class2 = models.ForeignKey(<Class>, on_delete=models.CASCADE) 
            Example Output: 
             {example} 
        
        6. Use is_calculated field in the test json object if the class of that object is inhererting from CalculationModel, in our case those models are Report and Upload models
        7. When you upload a file with a create test by assigning is_calculated to IN_PROGRESS, There is no need for an extra update test for that calculation which is being triggered by the file upload
        8. Build upon the test jsons that were already provided to you 
        9. No delete test cases
        10. Use the data available from previous tests, you don't have to create new data for the tests (build on top of the existing data)
        11. If a test has file_input field, you can just used that to upload the data, and use the data for the next tests so don't define any data of your own
        12. Please no ```json
        
        
    **Example Test Json**:
    {example_output}

    The next test json to generate is: {json_to_generate[0]}
    
    {report_context}

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

def generate_test_python_jsons_alg(set_to_test, json_path, upload=False, path_to_file_input=None):
    template = f"""
from django.core.management import call_command
from lex.lex_app.tests.ProcessAdminTestCase import ProcessAdminTestCase
from lex_app import settings

class {"".join(set_to_test)}Test(ProcessAdminTestCase):
    test_path = "{json_path}"
       
    def test(self):
        pass
        
    """
    
    
    template_upload = f"""
import pandas as pd
from django.apps import apps
from lex_app import settings
from lex_app.tests.ProcessAdminTestCase import ProcessAdminTestCase


class {"".join(set_to_test)}Test(ProcessAdminTestCase):
    test_path = "{json_path}"
    
    def setUp(self):
        self.model_name = "{"".join(set_to_test).replace("Upload", "")}"
        self.input_file_path = "{path_to_file_input}"

        super().setUp()
        self.model = apps.get_model(settings.repo_name, self.model_name)
        self.upload_model = apps.get_model(settings.repo_name, self.model_name + "Upload")

    def test_upload_and_data(self):

        # Read original Excel data
        df = pd.read_excel(self.input_file_path)

        # Test database entries
        db_objects = self.model.objects.all()
        self.assertEqual(len(db_objects), len(df), "Number of records doesn't match input file")

        # Get model fields excluding primary key
        model_fields = [f.name for f in self.model._meta.fields if not f.primary_key]

        # Compare data
        for index, row in df.iterrows():
            db_obj = db_objects[index]  # Match by index instead of name

            # Check each field that exists in both DataFrame and model
            for field_name in model_fields:
                if field_name in df.columns:
                    db_value = getattr(db_obj, field_name)
                    file_value = row[field_name]

                    # Handle different data types
                    if pd.notna(file_value):  # Skip NA/None values
                        if isinstance(db_value, float):
                            self.assertAlmostEqual(
                                db_value,
                                float(file_value),
                                places=2,
                                msg="Mismatch in " + field_name + " for record " + index
                            )
                        else:
                            self.assertEqual(
                                db_value,
                                file_value,
                                "Mismatch in " + field_name + " for record " + index
                            )
 
    
    """
    if upload:
        return template_upload
    else:
        return template




async def generate_test_jsons(project):
    from lex_ai.metagpt.roles.JsonGenerator import JsonGenerator
    role = JsonGenerator(project)
    rsp = await role.run("START")

    return rsp.content
