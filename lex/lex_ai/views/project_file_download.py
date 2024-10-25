import os
from io import BytesIO

from django.http import FileResponse, JsonResponse
from django_sharepoint_storage.SharePointCloudStorageUtils import get_server_relative_path
from django_sharepoint_storage.SharePointContext import SharePointContext
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_ai.models.ProjectInputFiles import ProjectInputFiles
from lex.lex_ai.models.ProjectOutputFiles import ProjectOutputFiles

class ProjectFileDownload(APIView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        file_type = request.query_params.get('file_type', None)  # 'input' or 'output'
        file_field = request.query_params.get('field', 'file')   # Field name
        pk = request.query_params.get('pk', None)

        if not pk or not file_type:
            return JsonResponse({"error": "Missing 'pk' or 'file_type' in query parameters"}, status=400)

        # Determine the model based on the file type
        if file_type == 'input':
            model = ProjectInputFiles
        elif file_type == 'output':
            model = ProjectOutputFiles
        else:
            return JsonResponse({"error": "Invalid 'file_type'. Must be 'input' or 'output'."}, status=400)

        # Retrieve the instance
        try:
            instance = model.objects.get(pk=pk)
        except:
            return JsonResponse({"error": "File not found"}, status=404)

        # Retrieve the file
        file = getattr(instance, file_field)

        if not file:
            return JsonResponse({"error": "File field is empty"}, status=404)

        file_url = file.url

        # Handle different storage backends
        if os.getenv("STORAGE_TYPE") == "SHAREPOINT":
            shrp_ctx = SharePointContext()
            file = shrp_ctx.ctx.web.get_file_by_server_relative_path(get_server_relative_path(file_url)).execute_query()
            binary_file = file.open_binary(shrp_ctx.ctx, get_server_relative_path(file_url))
            bytesio_object = BytesIO(binary_file.content)
            return FileResponse(bytesio_object)
        elif os.getenv("STORAGE_TYPE") == "GCS":
            return JsonResponse({"download_url": file_url})
        else:
            # Local file storage
            if os.getenv("KUBERNETES_ENGINE", "NONE") == "NONE":
                file_url = file.url if not file.url.startswith('/') else file.url
            return FileResponse(open(file_url, 'rb'))