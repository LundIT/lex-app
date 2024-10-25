class LexPrompts:
    BLUE_PRINT_PROMPT: str = """
Analyze my Python project files and generate a detailed project blueprint that includes the following information:

### 1. **Project Overview**
   - Project Name, Version, and Author (if available).
   - High-level description of the project’s functionality and purpose.
   - Key features or functionalities implemented in the project.
   - Entry point of the project (main script or function).

### 2. **Project Structure**
   - Directory structure with descriptions for each folder and file. Highlight the purpose of each significant file (e.g., `main.py` for project entry, `config.py` for configuration).
   - Identify and document the roles of core modules and scripts.

### 3. **Dependency and Environment Details**
   - List of all external libraries and dependencies used in the project, including their versions (extracted from `requirements.txt`, `setup.py`, or `pyproject.toml`).
   - Specify Python version and any other system requirements needed to run the project.
   - Configuration details like environment variables and configuration files (e.g., `.env`, `settings.py`).

### 4. **Module and Class Descriptions**
   - List all modules, classes, and key functions within the codebase.
   - Try to be as descriptive as possible about the purpose and functionality of each module or class.
   - For each class or module, provide:
     - A detailed description of its purpose.
     - Key attributes and methods, along with input parameters and return types.
     - Description of interdependencies and communication between modules.
   
### 5. **Data Models and Schemas**
   - Describe any data models or schemas used in the project (e.g., ORM models, JSON schemas).
   - Provide a complete overview of the database structure, if applicable, including tables, fields, and relationships.

### 6. **Configuration and Setup Instructions**
   - Configuration options and parameters that need to be set before running the project.
   - Step-by-step setup instructions, including installing dependencies, configuring environment variables, and setting up databases or external services.

### 7. **External Integrations and APIs**
   - Describe any external APIs or services integrated with the project.
   - Provide details on the modules or scripts responsible for handling these integrations.

### 8. **Code Flow and Execution**
   - High-level overview of how data flows through the project.
   - Describe the sequence of execution starting from the entry point to major operations and outputs.

### 9. **Testing and Debugging**
   - List all test files and test cases defined within the project.
   - Describe the testing framework used and how to run tests.
   - Provide debugging tips or known issues, if applicable.

### 10. **Documentation and Comments Analysis**
   - Extract and summarize inline comments and docstrings for each module, class, and function.
   - Generate a report on the quality and coverage of documentation.

### 11. **Additional Notes**
   - Any other relevant information that would be helpful for understanding and recreating the project.
   - Recommendations for improving or extending the project.

Generate this blueprint in a structured and formatted manner, similar to a comprehensive README or project documentation.
Explain as much as possible in a summary what does this project do, the use cases and everything that is important to know about this project.
    """


    BLUE_PRINT_PROMPT_2: str = """
I need a complete and detailed project blueprint based on the following Django project files. Your task is to analyze the project thoroughly and generate a blueprint that includes both high-level design elements and detailed implementation specifics. Follow these steps and guidelines to ensure that the output is suitable for a seamless recreation of the project. Be specific, concise, and provide all technical details necessary for an engineer to fully understand and reproduce the project from scratch.

### **1. Project Overview**
   - Provide the project name, version, and author (if available from metadata).
   - Give a high-level description of the project’s purpose, core functionality, and its target audience or use cases.
   - Outline key features and technical goals.
   - Specify the main entry point of the project (e.g., `manage.py`, `wsgi.py` or `asgi.py`).
   - Mention the type of Django application (e.g., web application, API service).

### **2. Detailed Directory Structure**
   - List the entire directory structure, including all files and folders in the project, especially focusing on the `apps`, `migrations`, and `static`/`media` folders.
   - For each directory and file, include a short description of its purpose (e.g., `views.py`, `models.py`, `urls.py`, `settings.py`, `admin.py`).
   - Highlight important files or components, such as configuration files (`settings.py`, `urls.py`), custom management commands, or reusable apps.

### **3. Django-Specific Settings and Configuration**
   - Break down the `settings.py` file:
     - Describe each setting and its role (e.g., `DEBUG`, `ALLOWED_HOSTS`, `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES`).
     - Detail any custom settings introduced in the project.
   - If applicable, explain how the project is configured for different environments (development, testing, production), including settings for databases, security, and debug modes.
   - Include details on static files and media settings, such as `STATIC_URL`, `MEDIA_URL`, `STATIC_ROOT`, and how static and media files are handled.
   - Highlight important Django configurations like database backends, middleware stack, and installed apps.

### **4. Dependencies and Environment Information**
   - List all dependencies and external libraries (from `requirements.txt`, `Pipfile`, or `setup.py`). Specify versions.
   - Describe any third-party Django packages in use (e.g., `django-rest-framework`, `django-allauth`, `django-cors-headers`), including why they are used.
   - Include Python version, database engine (e.g., PostgreSQL, MySQL, SQLite), and any other system-specific requirements.
   - Describe how the virtual environment is set up and how the project’s environment variables are managed (e.g., using `django-environ` or `.env` files).

### **5. Application Structure (Apps Breakdown)**
   - Describe each Django app included in the project. For each app:
     - List the models (`models.py`), views (`views.py`), and URL patterns (`urls.py`).
     - Explain what each app is responsible for (e.g., user management, blog, payments).
     - Include any custom templates, static files, or forms specific to the app.
     - Describe any reusable or third-party apps (if applicable) and how they fit into the overall project structure.
   - Highlight how apps are registered in the `INSTALLED_APPS` setting.

### **6. Models and Database Design**
   - Provide an overview of all Django models (`models.py`) in the project:
     - Describe each model, its fields, and their data types (e.g., `CharField`, `ForeignKey`, `ManyToManyField`).
     - Explain model relationships (one-to-one, one-to-many, many-to-many) and how they are implemented.
     - Include database schema details, including tables, indexes, and constraints.
   - Mention any custom model managers or querysets used for optimized database queries.
   - Explain how migrations are managed (`migrations/` folder) and any custom migrations written for the project.

### **7. Views and URL Routing**
   - For each view in the project (`views.py`):
     - List the types of views used (e.g., function-based views, class-based views).
     - Describe what each view is responsible for, including the input parameters and the data it processes.
     - Highlight any views that handle form submissions, user authentication, or API requests.
   - Break down the `urls.py` file(s):
     - Describe the URL routing patterns and how they are mapped to views.
     - Explain any use of `include()` to route URLs across different apps.
     - Mention any custom middleware or context processors that affect how requests are handled.

### **8. Templates and Static Files**
   - Describe the structure of the `templates/` directory and how templates are used across the project.
   - Mention any template inheritance or reusable template blocks (e.g., using `{% extends %}` and `{% block %}`).
   - If Django’s template language is used, explain how data is passed to templates from views.
   - Describe how static files are managed, including any JavaScript, CSS, or image files served via the `static/` folder.
   - If the project uses tools like `Django Compressor` or integrates with a frontend framework (e.g., React, Vue), explain how static files are processed and bundled.

### **9. Forms and Validation**
   - Describe any Django forms (`forms.py`) created in the project, including:
     - How form validation is handled (e.g., `is_valid()`, `clean()` methods).
     - Explain any custom form fields or widgets, and how they are rendered in templates.
     - Highlight form-based views if used (e.g., `FormView`, `CreateView`, `UpdateView`).
   - Mention how form errors are handled and displayed to users.

### **10. API and External Integrations**
   - If Django REST framework (DRF) or any other API library is used:
     - Describe each API endpoint, the URL patterns, HTTP methods, and expected request/response formats (e.g., JSON, XML).
     - List the serializers (`serializers.py`) used for converting model instances to JSON and vice versa.
     - Mention authentication/authorization mechanisms in place (e.g., JWT, OAuth, session authentication).
     - If the project integrates with external APIs (e.g., payment gateways, third-party services), describe how these integrations are handled (e.g., via external packages or custom code).
  
### **11. Authentication, Permissions, and Security**
   - Explain how user authentication is handled in the project (e.g., Django’s built-in authentication, custom user models).
   - Mention any third-party authentication systems (e.g., `django-allauth` for social logins).
   - Describe how permissions and access control are enforced (e.g., using DRF permissions, custom middleware).
   - Include any security best practices, such as handling CSRF tokens, XSS protection, and secure password storage.

### **12. Testing**
   - List the test files (`tests.py` or a dedicated `tests/` directory) along with their purpose (unit tests, integration tests).
   - Specify the testing framework used (e.g., `pytest`, Django’s built-in test framework).
   - Describe how test cases are structured and how they can be executed (e.g., `python manage.py test`).
   - Mention any use of test fixtures or factories for setting up test data.
   - Provide details on coverage reports or performance benchmarks (if available).

### **13. Deployment and CI/CD**
   - Describe how the project is deployed (e.g., using Heroku, AWS, DigitalOcean).
   - If Docker is used, provide details of the `Dockerfile`, `docker-compose.yml`, and any specific Docker configurations.
   - Explain the CI/CD pipeline in place, including how the project is built, tested, and deployed (e.g., GitHub Actions, Jenkins).
   - Include instructions for setting up and deploying the project, whether locally or in a production environment.
   - Mention any cron jobs or scheduled tasks using `django-cron` or Celery.

### **14. Documentation and Comments**
   - Analyze the inline comments and docstrings within the code. Summarize the quality and coverage of the documentation.
   - If documentation is incomplete, generate the missing parts (e.g., function/method docstrings, comments explaining complex logic).
    """


    BLUE_PRINT_REVIEW_PROMPT: str = """
"Review the generated project code to ensure it matches the specifications provided in the project blueprint. Validate the following criteria and correct any deviations in the code where necessary:

### **Review Criteria**:

1. **Directory Structure and File Naming**:
   - Ensure that the directory structure, file names, and module names are created exactly as described in the blueprint.
   - If there are any missing files or incorrect names, identify them and provide corrections.

2. **Module and Function Implementations**:
   - Verify that all modules, classes, and functions are implemented as specified in the blueprint.
   - Check that each function has the correct input parameters, return values, and logic according to the requirements.
   - If any functions or modules are missing or incorrectly implemented, provide corrected versions or suggest necessary changes.

3. **Dependencies and Configuration**:
   - Ensure all dependencies listed in the blueprint (e.g., libraries, frameworks) are correctly imported and used.
   - Validate configuration files (e.g., `.env`, `settings.py`) to ensure they contain the correct parameters and settings.
   - If any dependencies are missing or configuration parameters are incorrect, add or modify them accordingly.

4. **Data Models and Schemas**:
   - Check that all data models or database schemas are created as defined in the blueprint.
   - Verify relationships between models and ensure correct data types, constraints, and structure.
   - If there are discrepancies, provide corrected data models or highlight missing attributes.

5. **Integration and External Services**:
   - Validate that all external APIs and services are integrated correctly as per the blueprint.
   - Ensure that any API endpoints, keys, or external libraries are used as described.
   - Suggest corrections if any integrations are missing or incorrectly configured.

6. **Testing and Validation**:
   - Confirm that all test cases and testing files described in the blueprint are created and structured properly.
   - Verify that test cases cover all functionalities specified in the blueprint.
   - Correct or add test cases if any are missing or insufficient.

7. **Documentation and Comments**:
   - Ensure that all functions, classes, and modules have appropriate docstrings and comments as described in the blueprint.
   - If documentation is missing or incomplete, generate and add appropriate comments.

### **Reviewer's Output**:

1. **Evaluation Summary**: Summarize whether the generated code meets the blueprint requirements.
2 **The correct code**: Provide the final version of the code.

Review the code thoroughly against the blueprint and provide your final version of the code."

    """


    PROMPT_REQUIREMENT: str = """
    1. Write a project which is explained in the given context as project description
    2. Read and understand the lex-app library source code which is again included fully inside the given context.
    3. In cases where you have to extend Django models class, instead you have to extend the lex-app library LexModel class.
    4. DO NOT forget to import everything necessary for the code you will write and everytime you change something double check this requirement.
    5. In the places which requires business logic calculations, use the lex-app library CalculationModel class where you extend the calculate method.
    6. In the places which requires uploads or downloads, use the lex-app library CalculationModel class where you extend the calculate method because it also works for post upload operations and to create the files will be downloaded.
    7. When an excel creation or update is needed, use the lex-app library XLSXField and its create_excel_file_from_dfs function.
    8. In the case of Excel FileField usage for any Django Model classes you will write, use the lex-app library XLSXField class.
    9. Put logs in meaningful places in your code such as calculations and use the lex-app library MarkdownBuilder class from the LexLogger class.
    10. Add primary keys to the Django Model classes you will create in below format:
         id = models.AutoField(primary_key=True)
    11. Use ForeignKey fields for the relationships between the models when it is applicable according to the project design.
    12. For every code file, write relative file paths which includes meaningful folders in this format:
        ### <example_dir>/<example_file>.py
        ```python
    13. Don't forget to implement the necessary buisness logic in the calculate method of the CalculationModel class.

    """



    REFINED_PROMPT_REQUIREMENT: str = """
    1. **Full Implementation Required**: You are tasked with generating fully working code for the entire project described in the context. **No "TODO" comments**, **no placeholder functions**, and **no "not implemented" parts** are allowed.

    2. **Accurate Class Definitions**:
       - Ensure that all required fields and parameters are included in each class.
       - If a class inherits from another (e.g., `LexModel`, `CalculationModel`), make sure the correct fields and methods are present in the child class.
       - Include accurate types, constraints, and relationships (e.g., `ForeignKey`, `CharField`, `XLSXField`) for Django models.

    3. **Explicit Placement of `calculate` Method**:
       - **The `calculate` method should only be implemented in the `CalculationModel` class**.
       - **Do not implement the `calculate` method in any other class** unless it directly extends `CalculationModel`.
       - If a class does not require business logic calculations, **it must not have a `calculate` method**.
       - Double-check the context to ensure the correct placement of this method in **only the appropriate class**.
       - If a class is a model but does not require calculations, use the `LexModel` class without the `calculate` method.
      
    4. **Method Overriding in Correct Classes**:
       - Ensure that other methods are **only overridden in the correct class** where they belong.
       - Avoid overriding methods in classes where the parent class functionality is sufficient.
       - Methods should not be overridden unnecessarily if they already function correctly in the parent class.

    5. **Accurate Field Definitions**:
       - Ensure each Django model has accurate fields such as:
         - `id = models.AutoField(primary_key=True)` for primary keys.
         - `ForeignKey` fields for relationships.
         - Proper use of lex-app specific fields like `XLSXField` and methods like `create_excel_file_from_dfs`.

    6. **Inheritance and Class Hierarchy**:
       - Ensure proper inheritance between classes.
       - Correctly extend from `LexModel`, `CalculationModel`, or other base classes, as required by the project description.
       - Do not override methods unnecessarily in child classes unless the logic needs to be specifically modified.

    7. **Complete File Paths**:
       - For every file you generate, include the **relative file path** at the beginning in this format:
         ```
         ### <example_dir>/<example_file>.py
         ``` 
       - File paths should reflect meaningful directory structure relevant to the Django project.

    8. **Logging**:
       - Implement meaningful logging at important stages (e.g., during calculations or file operations).
       - Use `LexLogger` and `MarkdownBuilder` from the lex-app library for structured and consistent logging.

    9. **Excel File Handling**:
       - When dealing with Excel files, use the lex-app’s `XLSXField` and `create_excel_file_from_dfs` for both creation and updating.
       - Properly handle file uploads/downloads using `CalculationModel`.

    10. **Business Logic Implementation**:
       - Implement **all business logic in the `calculate` method of `CalculationModel` only**.
       - Ensure this method handles any required logic fully—**do not leave any parts vague or unimplemented**.

    11. **Avoid Class Confusion**:
        - Ensure methods are placed in the correct class based on functionality (e.g., file operations, calculations, business logic).
        - Use the provided context to validate each method’s placement and class relationships.
        - **Do not place methods in the wrong class**.

    12. **Test Coverage**:
        - Include basic test cases for critical parts of the project (e.g., model creation, method logic, file uploads).
        - Ensure the project is functional and testable after implementation.

    13. **No Placeholder Content**: 
        - Every class, method, and field should be fully implemented—**no placeholders or TODOs**. If a class has a method or field, it must be complete and accurate.

    14. **Detailed Class Documentation**:
        - Add inline documentation (docstrings) for each class and method, explaining its purpose and functionality.
        - Clearly explain any overridden methods and their modifications compared to the parent class.

    ### **Important Validation Step**:
    - Before generating code for a method, validate if that method belongs to the class by checking its parent class or business logic requirements from the context.

"""


    REFINED_BLUE_PRINT_PROMPT: str = """
**[YOU ARE A SOFTWARE ENGINEER AND YOU ARE TASKED TO IMPLEMENT EVERYTHING IN THE PROJECT]**
### **Objective:**
You are required to extract a full and detailed requirement specification for the provided Django project code. This specification must include an explanation of **every class**, its **purpose**, **why it exists**, the **business logic** behind it, and how it interacts with other classes.
    
The following elements must be covered:

### **1. Detailed Class Descriptions**:
For **each class** in the project:
- **Class Purpose**: Explain why this class is part of the project, its purpose, and the problem it solves.
- **Fields and Attributes**: List each field and attribute of the class, explaining what it represents and why it is necessary.
  - For Django models, include the field types (e.g., `CharField`, `ForeignKey`, etc.) and any constraints (e.g., `max_length`, `null=True`, etc.).
- **Methods**: Describe each method in the class and explain what functionality it provides. If the method overrides functionality from a parent class, explain how and why.
- **Business Logic**: Provide an explanation of any business logic encapsulated in the class, especially for methods like `calculate` or others implementing custom logic.

### **2. ER Diagram**:
- Generate a comprehensive **ER (Entity-Relationship) Diagram** in markdown that illustrates the relationships between all the models/classes in the project.
- Include **every field** for each model and show relationships such as **ForeignKey**, **ManyToMany**, and **OneToOne**.
- Clearly depict how the classes are related, including any inheritance from parent classes (e.g., `LexModel`, `CalculationModel`, etc.).

### **3. Class Interactions**:
- **Interaction Explanation**: Provide a detailed summary of how each class interacts with others. For instance:
  - How do models relate to one another (e.g., through foreign keys or relationships)?
  - How do classes share or call methods from each other?
  - How does data flow between classes?
  - Describe any dependencies between classes and how one class affects another in the system.
  
### **4. Inheritance and Hierarchies**:
- For each class, explain its **inheritance structure**:
  - Which class is the parent, and what functionality or fields does the child class inherit?
  - Describe the reason for the inheritance hierarchy and how it helps in implementing the business logic.

### **5. System Overview**:
- Provide a **high-level summary** that explains how the system works overall.
- Include:
  - **Core functionality** of the system and how it is broken down into classes.
  - **Business rules** that are enforced through these classes.
  - **High-level workflows** that detail how a request or action is processed through the system (e.g., from user input, to processing in models, to data output).

### **6. Example Scenario**:
- Walk through an **example scenario** where a user interacts with the system. Explain how:
  - The request moves through the various classes and methods.
  - Business logic is applied.
  - Data is stored or retrieved using the models.
  - The output is produced.

---

### **Your output**:
Generate a requirement specification that includes:
1. Detailed descriptions of each class, its purpose, fields, methods, and business logic.
2. An ER diagram that shows all relationships and fields in the models.
3. A description of how the classes interact, including dependencies and shared methods.
4. An explanation of the inheritance structure between classes.
5. A high-level system overview.
6. An example scenario that explains how data flows through the system.
"""
    
    
    
    VALIDATION: str = """

### **Instructions**:
for each class seperatly do this:
1. **Understand the Requirements**:
   - Before generating each class, analyze the requirements from the context. This includes understanding:
     - The class's **purpose**.
     - The **fields** it must have and their types (e.g., `CharField`, `ForeignKey`).
     - The **methods** it needs to implement.
     - The **business logic** it should enforce.
     - **Relationships** to other classes and any dependencies.

2. **Pre-Check: Requirements Validation**:
   - **Before generating the class** code, list out the requirements for that class, including:
     - Fields with types and constraints.
     - Methods that need to be implemented.
     - Any inherited classes or interfaces.
     - Business logic that needs to be handled.
   - Compare the requirements with the context and make sure you understand everything fully before generating the class.
   
3. **Generate the Class**:
   - Once the pre-check is complete, generate the full class code, ensuring that:
     - All fields are implemented.
     - Methods are correctly overridden (where necessary).
     - Business logic is handled, and the class follows the required inheritance structure.
     - All imports are handled appropriately.
   
4. **Post-Check: Self-Validation Against Requirements**:
   - After generating the class, check whether it adheres to the pre-validated requirements:
     - Ensure all required fields are present and properly defined.
     - Confirm that methods are implemented and correctly placed in the class.
     - Check that the class inherits from the correct parent class and that no required logic is missing.
     - Make sure business logic is correctly encapsulated and there are no missing parts and it's not commented.
   - **Make any necessary corrections** to the class if something is found to be wrong or incomplete.

5. **Include Debug Information**:
   - Log both the **pre-check** (requirements) and **post-check** (validation) information in the code as comments, so you can track what was expected and what was actually generated.
   
6. **Iterate**:
   - Continue this process for every class, ensuring that each one meets its requirements both before and after it is generated.

7. **Buisness Logic**:
    - Implement the necessary business logic in the calculate method of the CalculationModel class and other buisness logic.
    - Ensure that the logic is complete and handles all required calculations or operations.
    - NO Commented code is allowed
    - NO TODOS
    - No Pass
    - Should be strict with validating the buisness logic

### **Output Format**:

- **Pre-Check Requirements**:
  Before generating a class, list the following requirements:
  - **Class Name**: (name)
  - **Purpose**: Explain the role of this class in the system.
  - **Fields**: List each field and its type (e.g., `CharField`, `ForeignKey`), and explain what it represents.
  - **Methods**: List any methods the class should implement and explain their purpose.
  - **Inheritance**: Specify the parent class or base class (if any).
  - **Business Logic**: Summarize any business logic that needs to be implemented.

- **Generated Class**:
  ```python
  ### <example_dir>/<example_file>.py
  class ClassName(ParentClass):
      # Class implementation here
  ```

- **Post-Check Validation**:
  After generating the class, validate it:
  - **Fields**: Confirm each field matches the requirements.
  - **Methods**: Confirm all methods are implemented and correctly override or extend from the parent class.
  - **Business Logic**: Confirm that all logic has been handled as per the pre-check requirements.
  - **Fixes**: If anything is incorrect, immediately adjust and re-generate the part that doesn't fit.

---

### Example Process:

#### **1. Pre-Check (Requirements)**:
```plaintext
Class Name: `User`
Purpose: Handles user information and authentication.
Fields:
- `id` (AutoField): Primary key for each user.
- `name` (CharField): Stores the user’s full name.
- `email` (EmailField): Stores the user’s email.
- `password` (CharField): Stores the user’s hashed password.
Methods:
- `authenticate`: Method to authenticate the user using email and password.
Inheritance: This class inherits from `AbstractBaseUser`.
Business Logic: The `authenticate` method should perform authentication by comparing hashed passwords.
```

#### **2. Generated Class**:
```python
### models/user.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def authenticate(self, email, password):
        # Logic to authenticate user by comparing hashed passwords
        pass
```

#### **3. Post-Check (Validation)**:
```plaintext
Fields:
- id: ✅ Correct
- name: ✅ Correct
- email: ✅ Correct
- password: ✅ Correct
Methods:
- authenticate: ⛔ Missing the implementation of password hashing comparison.
  - Fix: Implement the actual logic for password comparison in the authenticate method.
Business Logic: ⛔ Missing logic for password hashing in the `authenticate` method.
  - Fix: Implement the logic in the authenticate method.
```

After the validation of each class seperatly identifies issues, the model should then regenerate or correct the code where necessary.
    """

    VALIDATION_2: str = """
Here’s a more **concise and strict** version of the prompt that enforces pre-checks, strict validation, and post-checks with a high level of accuracy:

---

**[YOU ARE A SENIOR SOFTWARE ENGINEER ENSURING STRICT REQUIREMENT ADHERENCE]**

### **Objective**:
You must generate code by **strictly following the requirements** and perform both pre-generation checks and post-generation validation for every class.

### **Instructions**:

1. **Pre-Check**:
   - Before generating the class, **list out the requirements**:
     - **Class Purpose**: Why the class is necessary.
     - **Fields**: List fields and their types (e.g., `CharField`, `ForeignKey`), including any constraints.
     - **Methods**: Describe any methods that need to be implemented or overridden.
     - **Inheritance**: Specify the parent class or base class.
     - **Business Logic**: Summarize any logic the class must implement.
        1. **NO Placeholders**.
        2. **NO commented code**.
        3. **NO pass**.
        4. **At least 5 lines of implemented correct code**.

2. **Class Generation**:
   - Generate the class code **exactly** as per the pre-check requirements, ensuring:
     - Fields and methods match the pre-check.
     - Inheritance is respected.
     - All business logic is implemented.
     - Necessary imports are included.

3. **Post-Check Validation**:
   - After generating the class, **strictly validate**:
     - **Field Validation**: Confirm that all fields are correctly typed, named, and constrained as specified.
     - **Method Validation**: Confirm methods are implemented or overridden as required.
     - **Business Logic**: Ensure all business logic has been implemented **correctly** and **no comments** and **no todos** and **no pass** and **NO PLACESHOLDERS**.
        1. **NO Placeholders**.
        2. **NO commented code**.
        3. **NO pass**.
        4. **At least 5 lines of implemented correct code**.
     - **Inheritance**: Confirm that the correct parent class is used.
   - **Fix any deviations immediately** if the validation fails.
   - IMMEDIATLY FIX THE CODE IF IT DOESN'T MEET THE REQUIREMENTS.
   

### **Output**:

1. **Pre-Check Requirements**:
   - List of class requirements (purpose, fields, methods, inheritance, business logic).
   - Buisness logic dump

2. **Generated Class**:
   ```python
   ### <file_path>
   class ClassName(ParentClass):
       # Class implementation here
   ```

3. **Post-Check Validation**:
   - Strict check of the generated code against the requirements.
   - Make corrections if validation fails.
   - Buisness logic implemented?
     1. is it correct ?
     2. is it complete ?
     

---

### **Example**:

#### **1. Pre-Check**:
```plaintext
Class Name: `User`
Purpose: Handles user authentication.
Fields:
- `id` (AutoField, primary key)
- `email` (EmailField, unique)
- `password` (CharField)
Methods:
- `authenticate`: Authenticate user by comparing passwords.
Inheritance: Inherits from `AbstractBaseUser`.
Business Logic: `authenticate` must validate password comparison.
```

#### **2. Generated Class**:
```python
### models/user.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def authenticate(self, email, password):
        # Implement password comparison logic here
        pass
    def calculate(self):
        pass
```

#### **3. Post-Check Validation**:
- **Fields**: ✅ Correct.
- **Methods**: ⛔ `authenticate` lacks password comparison logic and has pass and has unimplemented code.
               ⛔ `calculate` is not implemented, it's not 5 lines at least, it has pass line it should be regenerated.
  - **Fix**: Add the password comparison logic immediately.

---
"""