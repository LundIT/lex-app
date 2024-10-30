import os.path

from asgiref.sync import sync_to_async
from django.http import JsonResponse, StreamingHttpResponse
from lex.lex_ai.helpers.StreamProcessor import StreamProcessor
from lex.lex_ai.metagpt.generate_project_code import generate_project_code
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.models.Project import Project
from adrf.views import APIView
import asyncio

class ProjectCodeFile(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        path = request.query_params.get('path', "")
        with open(os.path.join(os.getenv("PROJECT_ROOT"), "DemoWindparkConsolidation", path), 'r') as file:
            code = file.read()
        return JsonResponse({'code': code})

    # async def post(self, request, *args, **kwargs):
    #     path = request.data.get('path', "")
    #     code = request.data.get('code', "")
    #     with open(os.path.join(os.getenv("PROJECT_ROOT"), "DemoWindparkConsolidation", path), 'w') as file:
    #         file.write(code)
    #     return JsonResponse({'message': 'Project code saved successfully'})

    async def patch(self, request, *args, **kwargs):
        path = request.data.get('path', "")
        code = request.data.get('code', "")
        with open(os.path.join(os.getenv("PROJECT_ROOT"), "DemoWindparkConsolidation", path), 'w') as file:
            file.write(code)
        return JsonResponse({'message': 'Project code saved successfully'})

