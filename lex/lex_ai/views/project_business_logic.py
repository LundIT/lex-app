from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex_ai.metagpt.generate_business_logic import generate_business_logic
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
import asyncio
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex.lex_ai.models.Project import Project

class ProjectBusinessLogic(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()

        business_logic = project.business_logic_calcs

        return JsonResponse({'business_logic': business_logic})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        files_with_analysis = project.files_with_analysis
        detailed_structure = project.detailed_structure
        models_and_fields = project.models_fields
        response = StreamingHttpResponse(StreamProcessor().process_stream(), content_type="text/plain")
        asyncio.create_task(generate_business_logic(detailed_structure, files_with_analysis, models_and_fields, project, user_feedback))
        return response

    async def patch(self, request, *args, **kwargs):
        business_logic = request.data.get('business_logic')

        project = await sync_to_async(Project.objects.first)()
        project.business_logic_calcs = business_logic
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Business logic saved successfully'})