import os
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.views import APIView
from django.http import JsonResponse
import requests
import git


class CloneRepo(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def get(self, request, *args, **kwargs):
        # url = f"https://{os.getenv('DOMAIN_BASE', 'melihsunbul.excellence-cloud.dev')}/api/github_access_token/"
        # headers = {
        #     'Authorization': f"Api-Key {os.getenv('LEX_API_KEY')}",
        #     'Content-Type': 'application/json'
        # }
        #
        # response = requests.get(url, headers=headers)
        # access_token = response.json()['access_token']
        repo = git.Repo.clone_from(f'https://<github_access_token>:x-oauth-basic@github.com/<your_github_username>/DemoWindparkConsolidation', f'{os.getenv("PROJECT_ROOT")}/temp_clone/DemoWindparkConsolidation')
        return JsonResponse({'message': "Project successfully cloned"})