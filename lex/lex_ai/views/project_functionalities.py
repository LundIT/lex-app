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

class ProjectFunctionalities(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

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
        user_feedback = request.data.get('user_feedback', "")
        files_with_analysis = project.files_with_analysis
        detailed_structure = project.detailed_structure
        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_project_functionalities(detailed_structure, files_with_analysis, project, user_feedback))
        return response

    async def patch(self, request, *args, **kwargs):

        project = await sync_to_async(Project.objects.first)()
        project.functionalities = request.data.get('functionalities')
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Functionalities saved successfully'})