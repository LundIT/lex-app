from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from lex.lex_app.auth_helpers import get_user_info, get_tokens_and_permissions
from django.apps import apps
from lex.lex_app import settings
import requests


class RBACInfo(APIView):
    """
    API view to retrieve RBAC (Role-Based Access Control) information.

    This view handles GET requests to provide information about user roles,
    role definitions, and user permissions.

    Attributes
    ----------
    http_method_names : list
        Allowed HTTP methods for this view.
    permission_classes : list
        Permissions required to access this view.
    """
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve RBAC information.

        This method processes the request to gather role definitions, user roles,
        and user permissions, and returns them in a JSON response.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        JsonResponse
            A JSON response containing user information, role definitions,
            user roles, and user permissions.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite

        # # Replace with the actual base URL of your server
        # base_url = 'https://melihsunbul.excellence-cloud.dev'
        #
        # # Replace with the actual keycloak_internal_client_id you want to use
        # keycloak_internal_client_id = 'e2280f8a-3ac4-4b12-beab-60556546add2'
        #
        # # Construct the full URL
        # url = f"{base_url}/api/clients/{keycloak_internal_client_id}/roles"
        #
        # # headers = {
        # #     'Authorization': f'Bearer {get_tokens_and_permissions(request)["confidential_access_token"]}',
        # # }
        #
        # headers = {
        #     'Authorization': f'Api-Key 763un7va.7gZEi2GYjl88lDWOenCGnYCRKEyEX0Y8',
        # }
        #
        # # Send the GET request
        # response = requests.get(url, headers=headers)
        #
        # # Check if the request was successful
        # if response.status_code == 200:
        #     # Parse and print the response (assuming it's in JSON format)
        #     roles = response.json()
        #     print(roles)
        # else:
        #     print(f"Failed to retrieve roles. Status code: {response.status_code}")
        #     print(response.text)

        role_definitions = {
            "admin": [{"action": "*", "resource": "*"}],
            "standard": [{"action": ["edit", "show", "export", "read", "list"], "resource": "*"}],
            "view-only": [{"action": ["show", "read", "list"], "resource": "*"}],
        }

        user_roles = ["admin"]
        user_permissions = []
        project_models = [model for model in
                              set(apps.get_app_config(settings.repo_name).models.values())]

        for model in project_models:
            try:
                user_permissions.append(model.evaluate_rbac())
            except Exception as e:
                pass
        # return JsonResponse(get_user_info(request))
        return JsonResponse({"user": get_user_info(request)["user"], "role_definitions": role_definitions, "user_roles": user_roles, "user_permissions": user_permissions})