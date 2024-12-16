import os

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.views import APIView
import requests
import git

class CommitAndPushView(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def post(self, request, *args, **kwargs):
        repo_path = f'{os.getenv("PROJECT_ROOT")}/temp_clone/DemoWindparkConsolidation'
        if not os.path.exists(repo_path):
            return JsonResponse({"error": "Repository path does not exist."}, status=400)

        files = request.data.get('files', [])
        message = request.data.get('message', '').strip()

        if not message:
            return JsonResponse({"error": "Commit message is required."}, status=400)

        try:
            repo = git.Repo(repo_path)
            if repo.bare:
                return JsonResponse({"error": "The repository is bare or invalid."}, status=400)

            if files:
                # Stage each file or handle deletion if it doesn't exist
                for f in files:
                    filepath = os.path.join(repo_path, f)
                    if os.path.exists(filepath):
                        # File exists, just add it
                        repo.index.add([f])
                    else:
                        # File does not exist, try to stage deletion
                        try:
                            repo.git.rm(f)
                        except:
                            # If rm fails, we ignore this file rather than throwing an error
                            pass
            else:
                # No files specified, add all changes including deletions
                repo.git.add('--all')

            # Now commit
            # Check if there are any changes to commit
            if not repo.index.diff("HEAD") and not repo.untracked_files:
                return JsonResponse({"error": "No changes to commit."}, status=400)

            repo.index.commit(message)

            # Push changes
            origin = repo.remotes.origin
            push_result = origin.push()
            for res in push_result:
                if res.flags & git.remote.PushInfo.ERROR:
                    return JsonResponse({"error": f"Push failed: {res.summary}"}, status=500)

            return JsonResponse({"success": "Changes have been committed and pushed successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
