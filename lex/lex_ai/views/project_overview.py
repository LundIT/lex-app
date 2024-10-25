import os
from io import BytesIO

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from lex.lex_ai.models.Project import Project


class ProjectOverview(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

    def get(self, request, *args, **kwargs):
        try:
            project = Project.objects.first()
        except:
            return JsonResponse({'error': "Project is not found"}, status=400)

        overview = project.overview

        return JsonResponse({'overview': overview})

    def post(self, request, *args, **kwargs):

        project = Project(overview=request.data.get('overview'))

        project.save()

        return JsonResponse({'message': 'Overview saved successfully'})