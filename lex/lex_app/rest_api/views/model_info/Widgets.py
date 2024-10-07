from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


class Widgets(APIView):
    """
    API view for handling widget-related requests.

    This view only supports the GET method and requires either an API key or
    user authentication to access.

    Attributes
    ----------
    http_method_names : list of str
        List of allowed HTTP methods for this view.
    permission_classes : list
        List of permission classes that are used to determine if the request
        should be granted.
    """
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get(self, *args, **kwargs):
        """
        Handle GET requests to retrieve widget structure.

        This method processes the admin site settings and returns the widget
        structure as a JSON response.

        Parameters
        ----------
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.

        Returns
        -------
        JsonResponse
            JSON response containing the widget structure.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite

        return JsonResponse({"widget_structure": processAdminSite.widget_structure})
