import os
from io import BytesIO

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.metagpt.generate_project_structure import generate_project_structure
from lex.lex_ai.models.Project import Project
from adrf.views import APIView
from lex.lex_ai.utils import global_message_stream
import asyncio

class ProjectStructure(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        structure = project.structure
        return JsonResponse({'structure': structure})


    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        overview = project.overview
        user_feedback = request.data.get('user_feedback', "")
        # Initialize an empty list to hold the structure
        file_structure = []

        # Fetch all input files
        input_files = await sync_to_async(list)(project.input_files.all())
        for input_file in input_files:
            file_structure.append({
                'name': input_file.file.name,  # Assuming file.name gives the file name
                'explanation': input_file.explanation,
                'type': 'Input'
            })

        # Fetch all output files
        output_files = await sync_to_async(list)(project.output_files.all())
        for output_file in output_files:
            file_structure.append({
                'name': output_file.file.name,  # Assuming file.name gives the file name
                'explanation': output_file.explanation,
                'type': 'Output'
            })

        response = StreamingHttpResponse(global_message_stream(), content_type="text/plain")
        asyncio.create_task(generate_project_structure(overview, file_structure, project, user_feedback))

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
