import os

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


class ProjectInfo(APIView):
    """
    API view to retrieve project information.

    This view requires either an API key or user authentication to access.
    """
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get(self, request, *args, **kwargs):
            """
        Handle GET requests to retrieve project information.

        Parameters
        ----------
        request : Request
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            A response object containing project information.
        """
            result = {"project_name": os.getenv("LEX_SUBMODEL_NAME"),
                      "branch_name": os.getenv("LEX_SUBMODEL_BRANCH"),
                      "environment": os.getenv("DEPLOYMENT_ENVIRONMENT")}
            return Response(result)