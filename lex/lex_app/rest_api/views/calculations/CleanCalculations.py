from django.apps import apps
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from lex_app.lex_models.CalculationModel import CalculationModel
from lex_app.settings import repo_name


class CleanCalculations(APIView):
    """
    API view to clean calculation records.

    This view handles POST requests to clean calculation records based on the provided data.
    It checks if the records are not in progress and adds them to the list of records to be cleaned.

    Attributes
    ----------
    http_method_names : list of str
        Allowed HTTP methods for this view.
    permission_classes : list
        Permissions required to access this view.
    """
    http_method_names = ['post']
    permission_classes = [HasAPIKey | IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to clean calculation records.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object containing the data.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        JsonResponse
            A JSON response containing the list of records to be cleaned.
        """
        will_be_cleaned = []

        for entry in request.data["records"]:
            # Parse JSON and extract the model name and record ID
            model_class = apps.get_model(repo_name, entry['model'])

            try:
                obj = model_class.objects.get(pk=entry['record_id'])

                if hasattr(obj, 'is_calculated') and obj.is_calculated != CalculationModel.IN_PROGRESS:
                    will_be_cleaned.append(f"{entry['model']}_{entry['record_id']}")

            except Exception as e:
                will_be_cleaned.append(f"{entry['model']}_{entry['record_id']}")

        return JsonResponse({"records": will_be_cleaned})
