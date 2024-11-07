from django.http import JsonResponse
from rest_framework.views import APIView


class RunMigrations(APIView):
    # permission_classes = [IsAuthenticated | HasAPIKey]

    def post(self, request, *args, **kwargs):
        from django.core.management import call_command
        project_name = request.data.get('project_name')
        try:
            call_command("makemigrations", project_name)
            call_command("migrate", project_name)
        except Exception as e:
            print(f"Migration error: {e}")
            return JsonResponse({"success": False})
        return JsonResponse({"success": True})


