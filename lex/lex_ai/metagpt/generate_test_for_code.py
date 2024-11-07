import yaml

from lex_ai.metagpt.LexContext import LexContext
from lex_ai.metagpt.TestContext import TestContext
from lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from lex_ai.metagpt.roles.LLM import LLM


async def generate_test_for_code(generated_code, project, import_pool, test_to_generate, test_class_name, dependencies):
    role = LLM()
    melih_prompt = f"""
Models that will be tested
Classes to test: {", ".join(test_to_generate)}

Project Context  
0. Project Overview and Structure with Business Logic:  
{project.overview}  
{project.detailed_structure}  
{project.business_logic_calcs}  

1. Relevant code for the test:  
{generated_code}

1.1. Imports for Model Definitions:  
{import_pool}

2. Data Processing:  
- Excel file upload handling  
- Data transformation logic  
- Report generation  

3. Sample Data Structure and Path for Testing Files:  
{project.files_with_analysis}  

Test Requirements

Please generate Django tests that cover:

1. Model Testing:  
   - Field validations (required fields, field types, constraints)  
   - Foreign key relationships  
   - Model methods  
   - Data integrity  

2. Excel Processing:  
   - File upload validation  
   - Data parsing accuracy  
   - Error handling for invalid data  
   - Column mapping verification  
   - Analyze real Excel files provided in **Project Context** (point 3) by reading them from their paths for correct row count, column names, and accurate assertion checks  
    
3. Business Logic (most important):  
   - Calculation accuracy  
   - Data transformation correctness  
   - Handling of edge cases  
   - Error scenarios  

4. Integration Testing:  
   - End-to-end workflow  
   - Database interactions  
   - File I/O operations  
   - Use real data and paths provided in **Project Context** for file I/O tests and assertions based on actual file contents  

Technical Specifications:  
- Use `django.test.TestCase`  
- Include `setUp` and `tearDown` methods  
- Use appropriate test fixtures  
- Follow Django testing best practices  
- Use `assertQuerysetEqual` for model comparisons  
- Use real data and operations, avoiding mocks  
- Models should be only imported from the import pool

Constraints:  
1. Only include tests for `{", ".join(test_to_generate)}` and its dependencies, if any. If there are no dependencies, avoid testing other model classes.  
2. Use accurate row counts, column names, and other details from the real Excel files provided in the **Project Context** to ensure correct assertions.  
3. Avoid any assumptions not based on provided information.  
4. If you want to do an assertion check, be sure that you know what to expect for every value you check (e.g. you don't know the second parameter in this example: self.assertEqual(len(df), 2) where df is coming from a file, and you don't know the exact number of rows).
5. **NEVER WRITE ON TOP THE FILE PATHS PROVIED THEY ARE READ ONLY** 
6. If you want to write to a file for any reason, use a temporary file path in the same folder and write there.

Test Structure Example:
```python
from lex.lex_app.tests.ProcessAdminTestCase import ProcessAdminTestCase

class {test_class_name.replace('_', '')}(ProcessAdminTestCase):
    @classmethod
    def setUp(self):
        super().setUp() 


    def test_[specific_functionality](self):
        # Test implementation
        pass

Generate Django the next django for my project following this exact format:
### Tests/{test_class_name.replace('_', '')}.py
```python


Only generate the test for the specified classes {", ".join(test_to_generate)} and stop.
[Test code here]
"""

    prompt = f"""
   Lex App Context:
    Key classes and their Required Imports:
        {yaml.dump(LexContext()._prompts)} 


    Usage example:
        ```
        ClassModel(LexModel):
            # Implement fields here
            # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
            # classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE)
            # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
            # Example of wrong foreign key:  models.ForeignKey('ClassModel2', on_delete=models.CASCADE) It should be the class itself not a string
            
        ClassModelUpload(CalculationModel):
            # Implement fields here
            # XLSXField here for file upload (Mandatory field in every CalculationModel)
            
            def calculate(self):
                logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
                logger.add_heading("ClassModel Data Upload", level=2)
                try:
                    # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                except Exception as e:
                    logger.add_paragraph(f"Error processing ClassModel data: str(e)")
                    raise e
                    
        def OutputReport(CalculationModel):
            # Implement fields here
            # XLSXField here for file report (Please don't forget this field in every CalculationModel)
            
            def calculate(self):
                logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True) 
                # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                

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
        
    Inner Import Pool:
    {import_pool} 


    Project Requirement (Just for context): 
        {LexPrompts().get_prompt("PROMPT_REQUIREMENT")}


    Generation requirement Context (Just for understanding the generated code):
        Before starting to generate the code, please read the following requirements:
            1. Only generate the next class and then stop generating.
            2. Use foreign key relationship for according to the data sample from: **Project Input and Output Files**
            2. No class Meta is allowed
            3. Don't use self.is_calculated or any implementation detail of LexApp class
            4. Use imports <Projectname>.<InBetweenFolders>.<class_name> or <Projectname>.<InBetweenFolders>.<function_name>
            5. Implement every method
            6. Use python convention for class names
            7. ONLY USE COLUMN NAMES FROM THE FILES INPUT AND OUTPUT CONTENT (THIS IS EXTREMELY IMPORTANT)
            8. You will get the folder hierarchy and the file names from the project structure (KEEP THAT IN MIND!!)
            9. start with and no other than ### path/to/class.py\nclass ClassName:
            10. Use import pool for importing classes of the project
            11. Calculation logic should be filled and implemented even if not provided in the project structure
    
    Project Input and Output Files:
        {project.files_with_analysis}
        
    When using data from files, use these:
    input_files:
        {project.input_files}
    output_files:
        {project.output_files}
        
    Generated code:
        {generated_code} 
     
    
    1. Understand the context of the project and write django test for the generated code.
    2. Write Test cases "from unittest import TestCase" for the generated code.
    3. Generate detailed tests with the existing samples for each class seperatly
    4. Your goal is to write tests according to project input and output file
    5. Understand the project from the context and write path of the tests in ### path format the whole tests inside ```python ,```
    
    Next test to generate is for class {test_to_generate}:
    """


    test_prompt = f"""
I need comprehensive Django tests for my project. Here's the detailed context:

## Model Under Test
Classes to test: {", ".join(test_to_generate)}

## Project Context
0. Project Overview and Structure and Business Logic:
{project.overview}
{project.detailed_structure}
{project.business_logic_calcs}

1. Model Definition:
{generated_code}


1.1 Imports to use for model definitions: 
{import_pool}

2. Data Processing:
- Excel file upload handling
- Data transformation logic
- Report generation

3. Sample Data Structure and Path for files for testing:
{project.files_with_analysis}

## Test Requirements

Please generate Django test that cover:

1. Model Testing:
- Field validations (required fields, field types, constraints)
- Foreign key relationships
- Model methods
- Data integrity

2. Excel Processing:
- File upload validation
- Data parsing accuracy
- Error handling for invalid data
- Column mapping verification
- Directly use the content of real files provided for testing in point (3.) of **Project Context** by reading the file from their path

3. Business Logic (most important):
- Calculation accuracy
- Data transformation correctness
- Edge cases handling
- Error scenarios

4. Integration Testing:
- End-to-end workflow
- Database interactions
- File I/O operations
- Directly use the content of real files provided for testing in point (3.) of **Project Context** by reading the file from their path

Technical Specifications:
- Use django.test.TestCase
- Include setUp and tearDown methods
- Use appropriate test fixtures
- Follow Django's testing best practices
- Use assertQuerysetEqual for model comparisons
- Do not mock anything and use real data and actions for testing

General remarks and Constraints:
- Do not include any test implementation for any other class other than the ones in **dependencies**: {", ".join(dependencies)}

Test Structure Example:
```python
from django.test import TestCase
from decimal import Decimal
import pandas as pd
import numpy as np
import io

class {test_class_name.replace('_', '')}(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup test data
        pass

    def setUp(self):
        # Setup test environment
        pass

    def test_[specific_functionality](self):
        # Test implementation
        pass

Generate Django the next django for my project following this exact format:
### Tests/{test_class_name.replace('_', '')}.py
```python


Only generate the test for the specified classes {", ".join(test_to_generate)} and stop.
[Test code here]
    """

    rsp = (await role.run(melih_prompt)).content
    return rsp

