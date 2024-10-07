from django.core.files.storage import default_storage
from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


class SharePointFileDownload(APIView):
    """
    API view for downloading files from SharePoint.

    Attributes
    ----------
    model_collection : None
        Placeholder for the model collection.
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
        Handle GET requests to download a file.

        Parameters
        ----------
        request : HttpRequest
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        FileResponse
            A response object containing the requested file.
        """
        model = kwargs['model_container'].model_class
        instance = model.objects.filter(pk=request.query_params['pk'])[0]
        file = instance.__getattribute__(request.query_params['field'])

        return FileResponse(default_storage.open(file.name, "rb"))