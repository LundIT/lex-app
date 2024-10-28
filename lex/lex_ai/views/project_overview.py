import os
from io import BytesIO

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from lex.lex_ai.models.Project import Project


class ProjectOverview(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def get(self, request, *args, **kwargs):
        project = Project.objects.first()
        if project:
            overview = project.overview
            return JsonResponse({'overview': overview})
        return JsonResponse({'overview': ''})

    def post(self, request, *args, **kwargs):

        project, created = Project.objects.get_or_create(id=1, defaults={'overview': request.data.get('overview')})

        if not created:
            project.overview = request.data.get('overview')
            project.save()

        return JsonResponse({'message': 'Overview saved successfully'})