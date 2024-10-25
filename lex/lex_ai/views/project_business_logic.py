import os
from io import BytesIO

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex_ai.metagpt.generate_business_logic import generate_business_logic
from openai import project
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.utils import global_message_stream
import asyncio
from lex.lex_ai.models.Project import Project

class ProjectBusinessLogic(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        business_logic = project.business_logic_calcs

        return JsonResponse({'business_logic': business_logic})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        files_with_analysis = project.files_with_analysis
        detailed_structure = project.detailed_structure
        models_and_fields = project.models_fields
        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_business_logic(detailed_structure, files_with_analysis, models_and_fields, project))
        return response