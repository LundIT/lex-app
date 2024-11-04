from asgiref.sync import sync_to_async
from lex.lex_ai.metagpt.roles.LLM import LLM
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex_ai.metagpt.LexContext import LexContext
from lex.lex_ai.metagpt.prompts.LexPrompts import LexPrompts
import yaml
from metagpt.roles.di.data_interpreter import DataInterpreter

async def conversation_file_operations(project, messages, user_feedback="", files=None):
    role = DataInterpreter(max_react_loop=1, tools=["<all>"], react_mode="react", code_result=True)

    prompt = f"""
        CONVERSATION CONTEXT:
        
        LEX APP CONTEXT:
 
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
        
        Project Current Generated Code:
            {project.generated_code}
        
        Attached Files:
        {files}

        User Prompt:
        {user_feedback}
        """

    rsp = (await role.run(prompt)).content
    return rsp

async def code_generation_conversation(project, messages, user_feedback="", files=None):
    role = LLM()

    prompt = f"""
    
    CONVERSATION CONTEXT:
    
    LEX APP CONTEXT:
 
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
        
        Project Current Generated Code:
            {project.generated_code}
        
        

        Conversation History:
        {messages}
        
        User Prompt:
        
        Attached Files:
        {files}
        
        {user_feedback}
    """
    if files:
        file_rsp = await conversation_file_operations(project, messages, user_feedback, files)
    rsp = (await role.run(prompt)).content
    # project.functionalities = rsp
    # await sync_to_async(project.save)()
    await StreamProcessor.global_message_queue.put("DONE")
    return rsp