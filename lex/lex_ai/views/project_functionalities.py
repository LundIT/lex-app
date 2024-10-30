from asgiref.sync import sync_to_async
from django.http import JsonResponse
from lex_ai.metagpt.generate_project_functionalities import generate_project_functionalities
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor

from django.http import StreamingHttpResponse

from lex.lex_ai.models.Project import Project

import asyncio

class ProjectFunctionalities(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        functionalities = project.functionalities

        return JsonResponse({'functionalities': functionalities})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        files_with_analysis = project.files_with_analysis
        detailed_structure = project.detailed_structure
        response = StreamingHttpResponse(StreamProcessor().process_stream(), content_type="text/plain")
        asyncio.create_task(generate_project_functionalities(detailed_structure, files_with_analysis, project, user_feedback))
        return response

    async def patch(self, request, *args, **kwargs):

        project = await sync_to_async(Project.objects.first)()
        project.functionalities = request.data.get('functionalities')
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Functionalities saved successfully'})