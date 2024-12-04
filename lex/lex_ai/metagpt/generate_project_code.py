import yaml

from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts
from asgiref.sync import sync_to_async
from lex.lex_ai.metagpt.LexContext import LexContext
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor


def generate_project_code_prompt(project, lex_app_context, code, class_to_generate, user_feedback="", import_pool="",
                                 stderr=None):
    stderr_context = '' if not stderr else f"""
    [TEST FAILURE ANALYSIS]
    Test Code: {stderr['test_code']}
    Implementation: {stderr['class_code']}
    Error: {stderr['error_message']}
    """

    prompt = f"""
    [CONTEXT ANALYSIS]
    1. Framework Components:
        {yaml.dump(LexContext()._prompts)}

    2. Project Scope:
        Overview: {project.overview}
        Core Functionalities: {project.functionalities}
        Business Logic: {project.business_logic_calcs}

    3. Data Architecture:
        Models and Fields: {project.models_fields}
        File Structure: {project.detailed_structure}
        Data Samples: {project.files_with_analysis}

    4. Available Project Components:
        Import Pool: {import_pool}
        Existing Code: {code}

    [IMPLEMENTATION REQUIREMENTS]
    Target Class: {class_to_generate[0]}
    File Path: {class_to_generate[1]}

    1. Base Class Extensions:
        - In cases where you have to extend Django models class, instead you have to extend the lex-app library LexModel class.
        - In the places which requires business logic calculations, use the lex-app library CalculationModel class where you extend the calculate method.
        - In the places which requires uploads or downloads, use the lex-app library CalculationModel class where you extend the calculate method because it also works for post upload operations and to create the files will be downloaded.


    2. Field Requirements:
        - Primary Key: models.AutoField(primary_key=True)
        - File Uploads: XLSXField
        - Foreign Keys: Use direct class references (ForeignKey(TargetClass, on_delete=models.CASCADE))

    3. Business Logic Implementation:
        - Mandatory calculate() method for CalculationModel
        - Structured error handling with logging
        - Data processing based on project specifications

    4. Logging Framework:
        - Use LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
        - Add meaningful log entries for operations
        - Structure logs with headings and paragraphs

    5. Code Organization:
        - Follow provided file structure
        - Use correct import paths: <ProjectName>.<Folder>.<ClassName>
        - Implement all required methods
        - Ensure proper error handling

    6. Data Integrity:
        - Use only column names from provided data samples
        - Implement proper relationships based on data structure
        - Ensure data validation

    [CRITICAL CONSTRAINTS]
    1. NO Meta classes
    2. NO self.is_calculated usage
    3. MUST implement calculate() method
    4. MUST use exact column names from samples
    5. MUST follow Python naming conventions
    6. MUST include all necessary imports

    {stderr_context if stderr else ""}

    {f"[USER FEEDBACK]:   {user_feedback}" if user_feedback else ""}

    [CODE GENERATION INSTRUCTIONS]
    1. Analyze requirements and data structure
    2. Identify necessary imports
    3. Design class structure
    4. Implement required methods
    5. Add proper error handling
    6. Include meaningful logging
    7. Verify against constraints

    Generate ONLY the requested class following this format:
    ### path/to/class.py
    <code>

    [START CODE GENERATION]
    """

    return prompt



def get_prompt_for_code_reflector():
    return f"""
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
            11. Calculation logic should be filled and implemented even if not provided in the project structure.
 
    """
def get_context_for_code_reflector(project):
    return f"""

        Lex App Context:
        Key classes and their Required Imports:
            {yaml.dump(LexContext()._prompts)} 


        Usage example:
            ```
            from <ProjectName>.<Folder>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
            ClassModel(LexModel):
                # Implement fields here
                # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
                classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE)
                # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
                # Example of wrong foreign key:  models.ForeignKey('ClassModel2', on_delete=models.CASCADE) It should be the class itself not a string
                
                # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                #    - Do not use: ModelClass.objects.get_or_create()
                #    - Do not use: ModelClass.objects.update_or_create()
                #    - Do not use: ModelClass.objects.get()
                #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                
            ```
            ClassModelUpload(CalculationModel):
                # Implement fields here
                # XLSXField here for file upload (Mandatory field in every CalculationModel)
                
                def calculate(self):
                    logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
                    logger.add_heading("ClassModel Data Upload", level=2)
                    try:
                        # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                        # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                        #    - Do not use: ModelClass.objects.get_or_create()
                        #    - Do not use: ModelClass.objects.update_or_create()
                        #    - Do not use: ModelClass.objects.get()
                        #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    except Exception as e:
                        logger.add_paragraph(f"Error processing ClassModel data: str(e)")
                        raise e
                        
            ```
            
            ```
            OutputReport(CalculationModel):
                # Implement fields here
                # XLSXField here for file report (Please don't forget this field in every CalculationModel)
                
                def calculate(self):
                    # logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True) 
                    # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                
                    # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                    #    - Do not use: ModelClass.objects.get_or_create()
                    #    - Do not use: ModelClass.objects.update_or_create()
                    #    - Do not use: ModelClass.objects.get()
                    #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    
                    from <ProjectName>.<Folder>.ClassModel import ClassModel # Since there is a foreign key relationship (or it's used somewhere)
                    class_model_objects = ClassModel.objects.all() # Example of using the foreign key relationship (ClassModel should therefor be imported)
                    
                    from <ProjectName>.<Folder2>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
                    class2_model_objects = ClassModel2.objects.all() # Example of using the foreign key relationship (ClassModel2 should therefor be imported)
                    
            ``` 

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
    """

def regenerate_project_code_prompt(project, lex_app_context, code, class_to_generate, user_feedback="",
                                     import_pool="", stderr=None, reflection_context=""):
    stderr_str = f"""
    [TEST FAILURE ANALYSIS]
    The class {class_to_generate['class']} failed this test:
    Test Code: {stderr['test_code']}
    Implementation: {stderr['class_code']}
    Error: {stderr['error_message']}
    Corrected Code (Not tested yet): {stderr['corrected_code']}    
    """


    prompt: str = f"""
    Lex App Context:
        Key classes and their Required Imports:
            {yaml.dump(LexContext()._prompts)} 


        Usage example:
            ```
            from <ProjectName>.<Folder>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
            ClassModel(LexModel):
                # Implement fields here
                # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
                classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE)
                # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
                # Example of wrong foreign key:  models.ForeignKey('ClassModel2', on_delete=models.CASCADE) It should be the class itself not a string
                
                # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                #    - Do not use: ModelClass.objects.get_or_create()
                #    - Do not use: ModelClass.objects.get()
                #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                
            ```
            ClassModelUpload(CalculationModel):
                # Implement fields here
                # XLSXField here for file upload (Mandatory field in every CalculationModel)
                
                def calculate(self):
                    logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
                    logger.add_heading("ClassModel Data Upload", level=2)
                    try:
                        # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                        # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                        #    - Do not use: ModelClass.objects.get_or_create()
                        #    - Do not use: ModelClass.objects.get()
                        #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    except Exception as e:
                        logger.add_paragraph(f"Error processing ClassModel data: str(e)")
                        raise e
                        
            ```
            
            ```
            OutputReport(CalculationModel):
                # Implement fields here
                # XLSXField here for file report (Please don't forget this field in every CalculationModel)
                
                def calculate(self):
                    # logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True) 
                    # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                
                    # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                    #    - Do not use: ModelClass.objects.get_or_create()
                    #    - Do not use: ModelClass.objects.get()
                    #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    
                    from <ProjectName>.<Folder>.ClassModel import ClassModel # Since there is a foreign key relationship (or it's used somewhere)
                    class_model_objects = ClassModel.objects.all() # Example of using the foreign key relationship (ClassModel should therefor be imported)
                    
                    from <ProjectName>.<Folder2>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
                    class2_model_objects = ClassModel2.objects.all() # Example of using the foreign key relationship (ClassModel2 should therefor be imported)
                    
            ``` 

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

    Import Pool (Double check the implementation against the imports at the end):
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
            11. Calculation logic should be filled and implemented even if not provided in the project structure.

    {"User Feedback:" if user_feedback else ""}
    {user_feedback}

    **Already Generated Code Context**: 
        {code}

    Reflection Context: 
    {reflection_context}
    
    The class to regenerate is: {class_to_generate['class']}
    The class path is: {class_to_generate['path']}

    Please just regenerate the class and stop according to the test and error code and then stop:

    [START REGENERATING CODE]
    """

    return prompt
def generate_project_code_prompt_old(project, lex_app_context, code, class_to_generate, user_feedback="", import_pool="", stderr=None):
    prompt: str = f"""
    Lex App Context:
        Key classes and their Required Imports:
            {yaml.dump(LexContext()._prompts)} 
    
    
        Usage example:
            ```
            from <ProjectName>.<Folder>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
            ClassModel(LexModel):
                # Implement fields here
                # Foreign key relationship should be used according to the data sample from: **Project Input and Output Files**
                classId = models.ForeignKey(ClassModel2, on_delete=models.CASCADE)
                # Example of wrong foreign key:  models.ForeignKey('<ProjectName>.<Folder>.ClassModel2', on_delete=models.CASCADE) Write only the class name
                # Example of wrong foreign key:  models.ForeignKey('ClassModel2', on_delete=models.CASCADE) It should be the class itself not a string
                
                # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                #    - Do not use: ModelClass.objects.get_or_create()
                #    - Do not use: ModelClass.objects.get()
                #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                
            ```
            ClassModelUpload(CalculationModel):
                # Implement fields here
                # XLSXField here for file upload (Mandatory field in every CalculationModel)
                
                def calculate(self):
                    logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True)
                    logger.add_heading("ClassModel Data Upload", level=2)
                    try:
                        # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                        # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                        #    - Do not use: ModelClass.objects.get_or_create()
                        #    - Do not use: ModelClass.objects.get()
                        #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    except Exception as e:
                        logger.add_paragraph(f"Error processing ClassModel data: str(e)")
                        raise e
                        
            ```
            
            ```
            OutputReport(CalculationModel):
                # Implement fields here
                # XLSXField here for file report (Please don't forget this field in every CalculationModel)
                
                def calculate(self):
                    # logger = LexLogger().builder(level=LexLogLevel.INFO, flushing=True) 
                    # Implement the logic here (Should always be implemented, never forget the logic anywhere)
                
                    # DO NOT USE THE FOLLOWING FUNCTIONS FROM ModelClass.objects (because if they are used with a Non-Unique key-value they return more than one object and it will cause an error):
                    #    - Do not use: ModelClass.objects.get_or_create()
                    #    - Do not use: ModelClass.objects.get()
                    #    for example instead you can use ModelClass.objects.filter(<key>=<Value>).first() and to check wheter the object is created or not you can use if not ModelClass.objects.filter(<key>=<Value>).exists():
                    
                    from <ProjectName>.<Folder>.ClassModel import ClassModel # Since there is a foreign key relationship (or it's used somewhere)
                    class_model_objects = ClassModel.objects.all() # Example of using the foreign key relationship (ClassModel should therefor be imported)
                    
                    from <ProjectName>.<Folder2>.ClassModel2 import ClassModel2 # Since there is a foreign key relationship (or it's used somewhere)
                    class2_model_objects = ClassModel2.objects.all() # Example of using the foreign key relationship (ClassModel2 should therefor be imported)
                    
            ``` 
    

         
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

    Import Pool (Double check the implementation against the imports at the end):
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
            11. Calculation logic should be filled and implemented even if not provided in the project structure.
    
    {"User Feedback:" if user_feedback else ""}
    {user_feedback}
    
    Already Generated Code: 
        {code}
     
    The next class to generate is: {class_to_generate[0]}
    The class path is: {class_to_generate[1]}

    
    Please just regenerate the class and stop according to the test and error code and then stop:
    
    [START GENERATING CODE]
    """

    return prompt


async def generate_project_code(project, user_feedback=""):
    from lex_ai.metagpt.roles.CodeGenerator import CodeGenerator
    from lex.lex_ai.metagpt.roles.CodeGenerator import ProjectInfo
    role = CodeGenerator(ProjectInfo(project, "DemoWindparkConsolidation"),  user_feedback)

    rsp = await role.run("START")

    project.generated_code = rsp.content
    await sync_to_async(project.save)()
    await StreamProcessor.global_message_queue.put("DONE")
    return rsp.content