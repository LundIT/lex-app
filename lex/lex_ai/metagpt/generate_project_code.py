import yaml

from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from asgiref.sync import sync_to_async
from lex.lex_ai.utils import global_message_queue
from lex_ai.metagpt.LexContext import LexContext


def generate_project_code_prompt(project, lex_app_context, code, class_to_generate, user_feedback="", import_pool=""):
    prompt: str = f"""
    Lex App Context:
        Key classes and their Required Imports:
            {yaml.dump(LexContext()._prompts)} 
    
    
        Usage example:
            ```
            def ClassModel(LexModel):
                # Implement fields here
                # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
                # classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE))
                # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
                
            def ClassModelUpload(CalculationModel):
                # Implement fields here
                # XLSXField here for file upload
                
                def calculate(self):
                    logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
                    logger.add_heading("ClassModel Data Upload", level=2)
                    try:
                        # Implement the calculation logic here
                    except Exception as e:
                        logger.add_paragraph(f"Error processing ClassModel data: str(e)")
                        raise e
                        
            def OutputReport(CalculationModel):
                # Implement fields here
                # XLSXField here for file report (Please don't forget this field in every CalculationModel)
                
                def calculate(self):
                    logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True) 
                    # Implement the logic here
                    
    
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
    
    
    Project Requirement: 
        {LexPrompts().get_prompt("PROMPT_REQUIREMENT")}
    
    
    Generation requirement:
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
    
    {"User Feedback:" if user_feedback else ""}
    {user_feedback}
    
    Already Generated Code: 
        {code}
    
    The next class to generate is: {class_to_generate[0]}
    The class path is: {class_to_generate[1]}
    
    [START GENERATING CODE]
    """
    print(prompt)

    return prompt


async def generate_project_code(project, user_feedback=""):
    from lex_ai.metagpt.roles.CodeGenerator import CodeGenerator
    role = CodeGenerator(project, user_feedback)

    rsp = await role.run("START")

    project.generated_code = rsp.content
    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    return rsp.content