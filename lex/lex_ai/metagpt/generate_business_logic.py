from asgiref.sync import  sync_to_async
from lex.lex_ai.metagpt.roles.LLM import LLM

from lex.lex_ai.rag.rag import RAG
from lex.lex_ai.utils import global_message_queue

async def generate_business_logic(project_structure, files_with_explanations, models_and_fields, project, user_feedback=""):
    role = LLM()

    rag = RAG()
    i, j = rag.memorize_dir(RAG.LEX_APP_DIR)
    lex_app_context = "\n".join([rag.query_code("LexModel", i, j, top_k=1)[0],
            rag.query_code("CalculationModel", i, j, top_k=1)[0],
            rag.query_code("LexLogger", i, j, top_k=1)[0],
            rag.query_code("XLSXField", i, j, top_k=1)[0]])


    prompt = f"""
    lex_app context:
    {lex_app_context} 

    File content and their explanations:
    {files_with_explanations} 

    Project Structure:
    {project_structure}
    
    Project Models and Fields:
    {models_and_fields}
    
    Current Project Business Logic:
    {"This is the first time for this query, there is no project business logic." if not user_feedback else project.business_logic_calcs}
    
    User Feedback:
    {"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

    [START INSTRUCTIONS]
    1. Given the project structure, describe and implement the business logic of the project in a markdown format.
    2. the lex_app is the framework to be used for the project structure
    2. The models and methods of the lex_app should only be used or extended not modeled 
    3. All the models extend either CalculationModel or LexModel depending on the functionality
    4. use LexLogger for logging
    5. Specify the inheritence if it exists
    6. Override the calculate method of CalculationModel for the classes that needs processing when needed
    7. Don't include fields from the CalculationModel or LexModel (only the fields that are specific to the project)
    8. If the model extends the CalculationModel, the calculate method should be overriden for either the processing or uploading of the data or both
    [STOP INSTRUCTIONS]
    **Output**:
        Return the business logic in a markdown format with no code snippets, just describe the logic in every calculation function of a specific class


    start of markdown:
    """

    rsp = (await role.run(prompt)).content
    project.business_logic_calcs = rsp
    await sync_to_async(project.save)()
    await global_message_queue.put("DONE")
    return rsp
