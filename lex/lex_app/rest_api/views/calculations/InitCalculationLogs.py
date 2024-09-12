import os

from django_sharepoint_storage.SharePointContext import SharePointContext
from django_sharepoint_storage.SharePointCloudStorageUtils import get_server_relative_path
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from django.http import JsonResponse

from lex.lex_app.logging.CalculationLog import CalculationLog
from lex.lex_app.logging.UserChangeLog import UserChangeLog
from lex_app.rest_api.signals import get_model_data


class InitCalculationLogs(APIView):
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get(self, request, *args, **kwargs):
        calculation_record = request.query_params['calculation_record']
        calculation_id = request.query_params['calculation_id']

        logs = get_model_data(calculation_record, calculation_id)

        return JsonResponse({"logs": logs})
