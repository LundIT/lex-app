import os

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.views import APIView
import requests
import git


class RepoStatus(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def get(self, request, *args, **kwargs):

        repo_path = f'{os.getenv("PROJECT_ROOT")}/temp_clone/DemoWindparkConsolidation'
        if not os.path.exists(repo_path):
            return JsonResponse({"error": "Repository path does not exist."}, status=400)

        try:
            repo = git.Repo(repo_path)
            if repo.bare:
                return JsonResponse({"error": "The repository is bare or invalid."}, status=400)

            # Run git status --porcelain to get file states
            status_output = repo.git.status('--porcelain')
            lines = status_output.split('\n') if status_output.strip() else []

            added_files = []
            changed_files = []
            deleted_files = []
            untracked_files = []

            for line in lines:
                if not line.strip():
                    continue
                # Line format: XY filename
                # X = index status, Y = working tree status
                # For example:
                #  M file.txt means modified in working tree
                # M  file.txt means modified in index (staged)
                # D  file.txt means deleted in index (staged deletion)
                #  D file.txt means deleted in working tree (not staged)
                # ?? file.txt means untracked
                index_status = line[0]
                worktree_status = line[1]
                filename = line[3:].strip()

                if index_status == '?' or worktree_status == '?':
                    # Untracked file
                    untracked_files.append(filename)
                elif index_status == 'A' or worktree_status == 'A':
                    # Added to index
                    # If you want to distinguish staged vs. unstaged add, check statuses more carefully.
                    added_files.append(filename)
                elif index_status == 'D' or worktree_status == 'D':
                    # Deleted
                    deleted_files.append(filename)
                elif index_status == 'M' or worktree_status == 'M':
                    # Modified
                    changed_files.append(filename)
                # You can handle other statuses as needed (R for renamed, etc.)

            status = {
                "changed_files": list(set(changed_files)),
                "untracked_files": list(set(untracked_files)),
                "added_files": list(set(added_files)),
                "deleted_files": list(set(deleted_files)),
                "branch": repo.active_branch.name,
            }

            return JsonResponse({"status": status})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

