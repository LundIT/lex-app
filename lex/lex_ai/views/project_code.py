import os
from io import BytesIO

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex_ai.metagpt.generate_project_code import generate_project_code
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.metagpt.generate_project_structure import generate_project_structure
from lex.lex_ai.models.Project import Project
from adrf.views import APIView
from lex.lex_ai.utils import global_message_stream
import asyncio

class ProjectCode(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

    async def get(self, request, *args, **kwargs):
        # if request.query_params.get('is_done') == "true":
        project = await sync_to_async(Project.objects.first)()
        code = project.generated_code
        return JsonResponse({'code': code})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_project_code(project, user_feedback))

        return response

    async def patch(self, request, *args, **kwargs):
        converted_data = {}
        folders = request.data['folders']
        for folder in folders:
            folder_name = folder['folderName']
            files_dict = {file['fileName']: file['description'] for file in folder['files']}
            converted_data[folder_name] = files_dict

        project = await sync_to_async(Project.objects.first)()
        project.structure = converted_data
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Structure saved successfully'})
