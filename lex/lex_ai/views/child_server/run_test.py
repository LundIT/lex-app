import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async
import subprocess
from django.core.management import call_command
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.models.Project import Project
from lex.lex_ai.metagpt.run_tests import run_tests


class RunTest(APIView):
    # permission_classes = [IsAuthenticated | HasAPIKey]

    async def post(self, request, *args, **kwargs):
        test_file_name = request.data.get('test_file_name')
        project_name = request.data.get('project_name')
        response = await sync_to_async(run_tests)(project_name, test_file=test_file_name)

        return JsonResponse(response)


