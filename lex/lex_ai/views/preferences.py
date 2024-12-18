from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from adrf.views import APIView
from lex_ai.models.PreferenceManager import PreferenceManager


class Preferences(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    async def get(self, request, *args, **kwargs):
        key = request.data.get('key', None)
        value = PreferenceManager.get_preference(key, None)

        return JsonResponse({'value': value})

    async def post(self, request, *args, **kwargs):
        key = request.data.get('key', None)
        value = request.data.get('value', None)
        if not key:
            PreferenceManager.set_preference(key, value)
        return JsonResponse({'message': 'Preference saved successfully'})
