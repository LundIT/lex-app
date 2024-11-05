from asgiref.sync import sync_to_async
from django.http import JsonResponse
from lex_ai.metagpt.code_generation_conversation import code_generation_conversation
from lex_ai.metagpt.generate_project_functionalities import generate_project_functionalities
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor

from django.http import StreamingHttpResponse

from lex.lex_ai.models.Project import Project

import asyncio

class CodeGenerationChat(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    # async def get(self, request, *args, **kwargs):
    #     project = await sync_to_async(Project.objects.first)()
    #
    #     functionalities = project.functionalities
    #
    #     return JsonResponse({'functionalities': functionalities})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        messages = request.data.get('messages', "")
        user_feedback = request.data.get('user_prompt', "")

        # Extract files from the request
        files = [file for file in request.FILES.values()]

        response = StreamingHttpResponse(StreamProcessor().process_stream(), content_type="text/plain")
        asyncio.create_task(code_generation_conversation(project, messages, user_feedback, files))
        return response

    # async def patch(self, request, *args, **kwargs):
    #
    #     project = await sync_to_async(Project.objects.first)()
    #     project.functionalities = request.data.get('functionalities')
    #     await sync_to_async(project.save)()
    #
    #     return JsonResponse({'message': 'Functionalities saved successfully'})