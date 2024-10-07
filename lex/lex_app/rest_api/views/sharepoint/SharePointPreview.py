import os

from django.http import JsonResponse
from django_sharepoint_storage.SharePointCloudStorageUtils import get_server_relative_path
from django_sharepoint_storage.SharePointContext import SharePointContext
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


class SharePointPreview(APIView):
    """
    API view to generate a preview link for a file stored in SharePoint.

    Attributes
    ----------
    model_collection : None
        Placeholder for model collection, not used in this implementation.
    http_method_names : list of str
        Allowed HTTP methods for this view.
    permission_classes : list
        Permissions required to access this view.
    """
    model_collection = None
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated]
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to generate a preview link for a SharePoint file.

        Parameters
        ----------
        request : HttpRequest
            The request object containing query parameters.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments, including 'model_container' which contains the model class.

        Returns
        -------
        JsonResponse
            A JSON response containing the preview link for the file.
        """
        model = kwargs['model_container'].model_class
        shrp_ctx = SharePointContext()
        instance = model.objects.filter(pk=request.query_params['pk'])[0]
        file = instance.__getattribute__(request.query_params['field'])

        file = shrp_ctx.ctx.web.get_file_by_server_relative_path(get_server_relative_path(file.url)).get().execute_query()
        preview_link = str(os.getenv('FILE_PREVIEW_LINK_BASE')) + "sourcedoc={" +file.unique_id +"}&action=embedview"



        return JsonResponse({"preview_link": preview_link})