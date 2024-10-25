import os
from io import BytesIO

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex_ai.metagpt.generate_project_functionalities import generate_project_functionalities
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.context import Context
from django.http import StreamingHttpResponse

from lex.lex_ai.models.Project import Project
from datetime import datetime

from metagpt.config2 import Config, config
from lex.lex_ai.utils import global_message_stream
import asyncio

class WriteSpecification(Action):
    name: str = "WriteSpecification"

    async def run(self, project_analysis: str):
        prompt1 = f"""
        Based on the following project analysis, write a detailed specification for the project in markdown:

        {project_analysis}

        Include:
        1. Explanation of the entire project (be as detailed as possible)
        2. Overall project structure
        3. Key components and their relationships
        4. Main functionalities
        5. Data models and their fields and how the column are called in the excel file.
        6. Business logic and calculations
        7. Real table names and field names from the printed field and connect to the classes in the project
        8. Emphasize on the correctness of the imports it needs to be always ProjectName.<class_name> or ProjectName.<function_name>
        Provide the specification in a structured format.

        Specification:
        """

        specification = await self._aask(prompt1, [
            "** [YOU ARE A SENIOR SOFTWARE ENGINEER TASKED WITH WRITING A DETAILED SPECIFICATION FOR THE PROJECT] **"
        ])
        return specification

class SpecificationWriter(Role):
    name: str = "SpecificationWriter"
    profile: str = "Expert in writing detailed project specifications"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSpecification])
        # self._watch([AnalyzeProject])

    async def _act(self) -> Message:
        print("-----------------------------------------------------------------------------------------------------")
        print("------------------------------------Specification Writer---------------------------------------------")
        project_analysis = self.get_memories(1)
        response = await self.rc.todo.run(project_analysis)

        # If you want to convert it to a string (assuming the content is text)
        # await save_to_file(specification,
        #                    f"specification/project_{self.context.kwargs.get('timestamp')}_specification.md")
        return Message(content=response, role=self.profile, cause_by=type(self.rc.todo))

class DesignArchitecture(Action):
    name: str = "DesignArchitecture"

    async def run(self, specification: str):
        prompt = f"""
        Based on the following project specification, design a high-level architecture for the project:

        {specification}

        Include:
        1. Component diagram
        2. Data flow diagram (please use diagram suited for llm model)
        3. Class hierarchy (if applicable) (please diagram suited for llm model)
        4. Database schema (if applicable) (please use diagram suited for llm model)
        5. File hierarchy (if applicable) (please use diagram suited for llm model)
        6. Seperate list of the classes that need to be generated in this format:
            - Classes = [Class1, Class2, Class3]

        Provide the architecture design in a structured format and in markdown.
        """

        architecture = await self._aask(prompt, [
            "** [YOU ARE A SENIOR SOFTWARE ARCHITECT TASKED WITH DESIGNING THE ARCHITECTURE OF THE PROJECT] **"
        ])
        return architecture

class ProjectArchitect(Role):
    name: str = "ProjectArchitect"
    profile: str = "Expert in designing software architecture"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([DesignArchitecture])
        self._watch([WriteSpecification])

    async def _act(self) -> Message:
        print("-----------------------------------------------------------------------------------------------------")
        print("------------------------------------Project Architect------------------------------------------------")
        specification = self.get_memories(1)
        architecture = await self.rc.todo.run(specification)
        # await save_to_file(architecture, f"architecture/project_{self.context.kwargs.get('timestamp')}_architecture.md")
        return Message(content=architecture, role=self.profile, cause_by=type(self.rc.todo))


class ProjectGenerationTeam(Team):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hire([
            # ProjectAnalyzer(),
            SpecificationWriter(),
            # ProjectArchitect(),
            # CodeGenerator(),
            # CodeReviewer(),
            # ProjectCreator(),
        ])
class ProjectFunctionalities(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]
    async def start_team(self, kwargs):
        project_path = "./DemoWindparkConsolidation"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context = Context(kwargs={"timestamp": timestamp, "project_path": project_path})
        team = ProjectGenerationTeam(context=context)
        team.invest(10000.01)
        team.run_project(idea=f"{project_path}")
        await team.run()

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        functionalities = project.functionalities
        # response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        #
        # asyncio.create_task(self.start_team(kwargs))
        #
        # return response

        return JsonResponse({'functionalities': functionalities})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        files_with_analysis = project.files_with_analysis
        detailed_structure = project.detailed_structure
        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_project_functionalities(detailed_structure, files_with_analysis, project))
        return response