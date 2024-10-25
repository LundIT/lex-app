import os
from io import BytesIO

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.metagpt.generate_model_structure import generate_model_structure
from lex.lex_ai.models.Project import Project
from lex.lex_ai.utils import global_message_stream
import asyncio

class ProjectModelFields(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

    async def get(self, request, *args, **kwargs):
        # if request.query_params.get('is_done') == "true":

        project = await sync_to_async(Project.objects.first)()
        models_fields = project.models_fields
        return JsonResponse({'model_and_fields': models_fields})
        #
        # else:
        #     project = await sync_to_async(Project.objects.first)()
        #     detailed_structure = project.detailed_structure
        #     response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        #     asyncio.create_task(generate_model_structure(detailed_structure, project))
        #     return response

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        detailed_structure = project.detailed_structure
        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_model_structure(detailed_structure, project, user_feedback))
        return response

    async def patch(self, request, *args, **kwargs):
        project = Project.objects.first()

        project.structure = request.data.get('structure')

        project.save()

        return JsonResponse({'message': 'Structure saved successfully'})
