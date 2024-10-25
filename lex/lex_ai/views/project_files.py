from django.http import JsonResponse
from rest_framework.views import APIView
from lex.lex_ai.models.Project import Project
from lex.lex_ai.models.ProjectInputFiles import ProjectInputFiles
from lex.lex_ai.models.ProjectOutputFiles import ProjectOutputFiles
from django.db import transaction
from django.core.exceptions import ValidationError
import json

class ProjectFilesView(APIView):
    # permission_classes = [IsAuthenticated, HasAPIKey]

    def get(self, request, *args, **kwargs):
        try:
            project = Project.objects.first()
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Fetch the input and output files
        input_files = list(project.input_files.values('id', 'file', 'explanation'))
        output_files = list(project.output_files.values('id', 'file', 'explanation'))

        # Return the relative file paths (as stored in the database)
        input_files = [{
            'uid': f["id"],  # Unique id for each file
            'name': f['file'].split('/')[-1],  # Extract the file name from the file path
            'url': f['file'],
            'explanation': f['explanation']
        } for f in input_files]

        output_files = [{
            'uid': f["id"],  # Unique id for each file
            'name': f['file'].split('/')[-1],  # Extract the file name from the file path
            'url': f['file'],
            'explanation': f['explanation']
        } for f in output_files]

        return JsonResponse({
            'overview': project.overview,
            'input_files': input_files,
            'output_files': output_files
        })

    def post(self, request, *args, **kwargs):

        # Get the project or return error
        project = Project.objects.first()
        if not project:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Process deletions and new uploads
        self.delete_files(request, project)
        self.save_files(request, project)

        project.save()

        return JsonResponse({'message': 'Project saved successfully', 'project_id': project.id})

    def get_project(self, project_id):
        """Fetches the project by ID."""
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None

    def delete_files(self, request, project):
        """Handles the deletion of input and output files."""
        deleted_input_files = json.loads(request.POST.get('deleted_input_files', '[]'))
        deleted_output_files = json.loads(request.POST.get('deleted_output_files', '[]'))

        if deleted_input_files:
            ProjectInputFiles.objects.filter(id__in=deleted_input_files).delete()
        if deleted_output_files:
            ProjectOutputFiles.objects.filter(id__in=deleted_output_files).delete()

    def save_files(self, request, project):
        """Handles the saving of input and output files and their descriptions."""
        input_files = self.save_file_group(
            request=request,
            project=project,
            file_key_prefix='input_files',
            description_key_prefix='input_files_description',
            model=ProjectInputFiles
        )

        output_files = self.save_file_group(
            request=request,
            project=project,
            file_key_prefix='output_files',
            description_key_prefix='output_files_description',
            model=ProjectOutputFiles
        )

        # Link new files to the project
        if input_files:
            project.input_files.set(input_files)
        if output_files:
            project.output_files.set(output_files)

    def save_file_group(self, request, project, file_key_prefix, description_key_prefix, model):
        """Saves a group of files and their descriptions."""
        file_objects = []
        index = 0

        while True:
            file_key = f'{file_key_prefix}_{index}'
            description_key = f'{description_key_prefix}_{index}'

            file_obj = request.FILES.get(file_key)
            description = request.POST.get(description_key, '')

            if file_obj or description:
                file_instance = model(file=file_obj, explanation=description) if file_obj else None
                if file_instance:
                    file_instance.save()
                    file_objects.append(file_instance)
            else:
                break  # No more files or descriptions found

            index += 1

        return file_objects
