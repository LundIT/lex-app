from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.metagpt.generate_model_structure import generate_model_structure
from lex.lex_ai.models.Project import Project
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
import asyncio

class ProjectModelFields(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):

        project = await sync_to_async(Project.objects.first)()
        models_fields = project.models_fields
        return JsonResponse({'model_and_fields': models_fields})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        detailed_structure = project.detailed_structure
        response = StreamingHttpResponse(StreamProcessor().process_stream(), content_type="text/plain")
        asyncio.create_task(generate_model_structure(detailed_structure, project, user_feedback))
        return response

    async def patch(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        model_and_fields_data = request.data.get('model_and_fields', {})

        project.models_fields = model_and_fields_data
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Models and fields are saved successfully'})
