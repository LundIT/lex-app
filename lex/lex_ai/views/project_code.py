import os

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex.lex_ai.metagpt.generate_project_code import generate_project_code
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.models.Project import Project
from adrf.views import APIView
import asyncio

from lex_ai.metagpt.generate_test_jsons import generate_test_jsons
from lex_ai.metagpt.roles.CheckpointManager import CodeGeneratorCheckpoint
from lex_ai.metagpt.roles.CodeGenerator import CodeGenerator


class ProjectCode(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        generated_code = project.generated_code
        checkpoint_manager = CodeGeneratorCheckpoint("DemoWindparkConsolidation")
        try:
            latest_checkpoint = await checkpoint_manager.restore_latest_checkpoint()
            directory_tree = latest_checkpoint.generate_tree()
        except FileNotFoundError as e:
            directory_tree = []

        return JsonResponse({'directory_tree': directory_tree})

    async def post(self, request, *args, **kwargs):
        project = await sync_to_async(Project.objects.first)()
        user_feedback = request.data.get('user_feedback', "")
        stream_processor = StreamProcessor(
            delimiter="```python",
            end_delimiter="```",
            max_buffer=20
        )
        asyncio.create_task(generate_project_code(project))
        response = StreamingHttpResponse(stream_processor.process_stream(trigger_enabled=True), content_type="text/plain")
        return response

    async def patch(self, request, *args, **kwargs):
        code = request.data.get('code')

        project = await sync_to_async(Project.objects.first)()
        project.generated_code = code
        await sync_to_async(project.save)()

        return JsonResponse({'message': 'Project code saved successfully'})

