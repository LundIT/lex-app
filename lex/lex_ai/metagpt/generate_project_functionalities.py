from asgiref.sync import  sync_to_async
from lex.lex_ai.metagpt.roles.LLM import LLM
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor

async def generate_project_functionalities(project_structure, files_with_explanations, project, user_feedback=""):

    role = LLM()

    better_prompt = f"""
File content and their explanations:
{files_with_explanations}

Project Structure:
{project_structure}

Current Project Functionalities:
{"This is the first time for this query, there is no project functionality." if not user_feedback else project.functionalities}

User Feedback:
{"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

[START INSTRUCTIONS]

Given the project structure, summarize the main functionalities of the project, listing each model with a high-level description of its role and key interactions.
1. Provide a basic pseudocode outline for each model’s calculate method (Upload and Report Model basically), mentioning:
    - Primary steps for data processing, report generation, and any conditional logic.
    - Any logging actions.
    - Simplified placeholders for complex calculations, with notes on intended outcomes.
    - Avoid specific implementation details; instead, focus on the sequence and purpose of steps in each model.
2. Present this information in markdown format without code snippets. 

[STOP INSTRUCTIONS]
Start of markdown:
    """

    prompt = f"""
    File content and their explanations:
    {files_with_explanations} 

    Project Structure:
    {project_structure} 
    
    Current Project Functionalities:
    {"This is the first time for this query, there is no project functionality." if not user_feedback else project.functionalities}
    
    User Feedback:
    {"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

    [START INSTRUCTIONS]
    1.Given the project structure, summarize the main functionalities of the project.
    2.Should be returned in a markdown format.
    3. No ```.
    [STOP INSTRUCTIONS]

    start of markdown:
    """

    rsp = (await role.run(better_prompt)).content
    project.functionalities = rsp
    await sync_to_async(project.save)()
    await StreamProcessor.global_message_queue.put("DONE")
    return rsp