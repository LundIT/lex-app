import yaml

from lex_ai.metagpt.LexContext import LexContext
from lex_ai.metagpt.TestContext import TestContext
from lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from lex_ai.metagpt.roles.LLM import LLM


async def generate_test_for_code(generated_code, project, import_pool, class_to_generate, tests):
    role = LLM()

    prompt = f"""
   Lex App Context:
    Key classes and their Required Imports:
        {yaml.dump(LexContext()._prompts)} 


    Usage example:
        ```
        def ClassModel(LexModel):
            # Implement fields here
            # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
            # classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE)
            # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
            # Example of wrong foreign key:  models.ForeignKey('ClassModel2', on_delete=models.CASCADE) It should be the class itself not a string
            
        def ClassModelUpload(CalculationModel):
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
    Generated code:
        {generated_code} 
    Written tests so far:
        {tests} 
     
    
    1. Understand the context of the project and write django test for the generated code.
    2. Write Test cases "from unittest import TestCase" for the generated code.
    3. Generate detailed tests with the existing samples for each class seperatly
    4. Your goal is to write tests according to project input and output file
    5. Understand the project from the context and write path of the tests in ### path format the whole tests inside ```python ,```
    
    Next test to generate is for class {class_to_generate}:
    """

    rsp = (await role.run(prompt)).content
    return rsp

