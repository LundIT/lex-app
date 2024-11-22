from asgiref.sync import  sync_to_async
from lex.lex_ai.metagpt.roles.LLM import LLM

from lex.lex_ai.rag.rag import RAG
from lex.lex_ai.metagpt.LexContext import LexContext
from lex.lex_ai.metagpt.TestContext import TestContext

from lex.lex_ai.helpers.StreamProcessor import StreamProcessor


async def generate_business_logic(project_structure, files_with_explanations, models_and_fields, project, user_feedback=""):
    role = LLM(system="""
You are Josh, a highly capable and analytical AI Software Engineer. Your task is to provide an accurate, detailed, and comprehensive description of the business logic for the given project. You will use the provided project context, structure, models, and any user feedback to inform your response. 
**Incorporate a clear chain-of-thought** in your reasoning to ensure transparency and comprehensiveness in your explanations. When describing the `calculate()` methods, provide **detailed and well-documented pseudo-code** that outlines each step of the calculation process.
    """)

    rag = RAG()
    i, j = rag.memorize_dir(RAG.LEX_APP_DIR)
    lex_app_context = "\n".join([rag.query_code("LexModel", i, j, top_k=1)[0],
            rag.query_code("CalculationModel", i, j, top_k=1)[0],
            rag.query_code("LexLogger", i, j, top_k=1)[0],
            rag.query_code("XLSXField", i, j, top_k=1)[0]])

    melih_prompt = f"""
   Lex_app context:
{LexContext()._prompts}

File content and their explanations:
{files_with_explanations}

Project Structure:
{project_structure}

Project Models and Fields:
{models_and_fields}

Accumulated Functionalities:
{project.functionalities}

User Feedback:
{"This is the first time for this query, there is no user feedback." if not user_feedback else user_feedback}

[START INSTRUCTIONS]

1. Given the project structure, enhance the basic pseudocode provided in the functionalities step by adding detailed business logic for each model’s calculate method. Incorporate specifics on data processing, complex calculations, and any conditional steps.
2. Include validation checks for each calculate method:
    - Confirm that each step in the pseudocode aligns with the intended functionality and business logic.
    - Cross-check that calculations, logging with LexLogger, and any necessary data transformations are included and correctly ordered.
    - Highlight any potential gaps or issues within the calculation logic.
3. Log any key operations as required by project guidelines using LexLogger.
4. Avoid including fields from CalculationModel or LexModel unless they are specific to this project.
5. Present the business logic in markdown format with only descriptive text (no code snippets).
6. Please add a user story or scenario that demonstrates the use of the business logic in a real-world context.

[STOP INSTRUCTIONS]
Start of markdown: 
    """
    better_prompt = f"""
### Guidelines:

- **Structure Your Response Using Markdown:**
  - Use level 2 headers (`##`) for main sections.
  - Use bolding (`**`) for subsections.
  
- **Content Requirements:**
  1. **Project Overview:**
     - Provide a brief summary of the project based on the provided context and structure.
  
  2. **Business Logic Description:**
     - For each class that extends `CalculationModel` or `LexModel`:
       - **Class Name:**
         - **Inheritance:** Specify the parent class (`CalculationModel` or `LexModel`).
         - **Logging:** Mention the use of `LexLogger` for logging activities.
         - **Fields:** Describe only the fields specific to the project (exclude inherited fields).
         
       - **Calculate Method:**
         - **Purpose:** Explain what the `calculate()` method is intended to achieve within the class.
         - **Chain-of-Thought Explanation:** Detail the step-by-step reasoning process that the method follows to perform its calculations.
         - **Pseudo-Code:** Provide a thorough and documented pseudo-code representation of the `calculate()` method, highlighting key operations and logic flows.
         
  3. **Inheritance and Overriding:**
     - Clearly specify any inheritance hierarchies and overridden methods, especially focusing on the `calculate()` methods where applicable.

- **Formatting Requirements:**
  - Use **unordered lists** for items.
  - Present comparisons in **markdown tables** for clarity.
  - Ensure all explanations are self-contained and do not require external references.
  
- **Style:**
  - Maintain an unbiased and journalistic tone.
  - Use italics for highlighting specific terms or phrases.
  - Avoid including URLs, links, or bibliographies.
  - Ensure the response is concise yet comprehensive, avoiding unnecessary repetition.

### Provided Data:

```
lex_app context:
{LexContext()._prompts} 
 

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
```

**[START INSTRUCTIONS]**
1. Based on the provided project structure, detail the business logic of the project in markdown format.
2. Utilize the `lex_app` framework as the foundation for the project structure.
3. Extend or utilize the existing models and methods of the `lex_app`; do not create new models.
4. Ensure all models extend either `CalculationModel` or `LexModel` based on their functionality.
5. Implement logging using `LexLogger`.
6. Specify inheritance relationships where they exist.
7. Override the `calculate` method of `CalculationModel` for classes that require processing, uploading of data, or both.
8. Exclude fields inherited from `CalculationModel` or `LexModel`, focusing only on project-specific fields.
9. For models extending `CalculationModel`, provide a detailed and documented pseudo-code implementation of the overridden `calculate()` method, illustrating how data processing or uploading is handled.

**[STOP INSTRUCTIONS]**

**Output**:
Return the comprehensive business logic in markdown format, incorporating detailed explanations and documented pseudo-code for every `calculate()` method within each relevant class. Ensure the response follows the formatting and style guidelines outlined above.

---

# Example Structure of the Refined Output

## Project Overview

Provide a brief summary of the project's purpose and functionality.

## Business Logic Description

### ClassName1
- **Inheritance:** CalculationModel
- **Logging:** Utilizes LexLogger for all logging activities.
- **Fields:**
  - `field1`: Description of field1.
  - `field2`: Description of field2.

- **Calculate Method:**
  - **Purpose:** Explain the objective of the `calculate()` method within this class.
  
  - **Chain-of-Thought Explanation:**
    1. Step 1: Describe the first step in the calculation process.
    2. Step 2: Explain the second step, including any conditional logic or data transformations.
    3. Step 3: Continue detailing each subsequent step until the calculation is complete.
  
  - **Pseudo-Code:**
    ```pseudo
    function calculate():
        // Initialize necessary variables
        initialize variables

        // Step 1: Description
        perform step 1 operations

        // Step 2: Description
        perform step 2 operations

        // Continue detailing each step with comments explaining the logic

        // Finalize and return the result
        return result
    ```

### ClassName2
- **Inheritance:** LexModel
- **Logging:** Utilizes LexLogger for all logging activities.
- **Fields:**
  - `fieldA`: Description of fieldA.
  - `fieldB`: Description of fieldB.

- **Calculate Method:**
  - **Purpose:** Explain the objective of the `calculate()` method within this class.
  
  - **Chain-of-Thought Explanation:**
    1. Step 1: Describe the first step in the calculation process.
    2. Step 2: Explain the second step, including any conditional logic or data transformations.
    3. Step 3: Continue detailing each subsequent step until the calculation is complete.
  
  - **Pseudo-Code:**
    ```pseudo
    function calculate():
        // Initialize necessary variables
        initialize variables

        // Step 1: Description
        perform step 1 operations

        // Step 2: Description
        perform step 2 operations

        // Continue detailing each step with comments explaining the logic

        // Finalize and return the result
        return result
    ```

## Inheritance and Overriding

| Class Name | Parent Class      | Methods Overridden |
|------------|-------------------|--------------------|
| ClassName1 | CalculationModel  | calculate()        |
| ClassName2 | LexModel           | calculate()        |

---

**Note:** Replace `ClassName1`, `ClassName2`, and other placeholders with actual class names and relevant details from your project. Ensure that each `calculate()` method's pseudo-code is thoroughly documented to reflect the precise logic and operations it performs.
    """

    prompt = f"""

    lex_app context:
    {LexContext()._prompts} 
     

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

    rsp = (await role.run(melih_prompt)).content
    project.business_logic_calcs = rsp
    await sync_to_async(project.save)()
    await StreamProcessor.global_message_queue.put("DONE")
    return rsp
