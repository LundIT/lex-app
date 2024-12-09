from django.urls import path

from lex_ai.views.child_server.run_migrations import RunMigrations
from lex_ai.views.child_server.run_test import RunTest
from lex_ai.views.project_files import ProjectFilesView

from lex_ai.views.project_overview import ProjectOverview
from lex_ai.views.project_file_download import ProjectFileDownload
from lex_ai.views.project_structure import ProjectStructure
from lex_ai.views.project_functionalities import ProjectFunctionalities
from lex_ai.views.project_business_logic import ProjectBusinessLogic
from lex_ai.views.project_model_fields import ProjectModelFields
from lex_ai.views.project_code import ProjectCode
from lex_ai.views.project_code_file import ProjectCodeFile
from lex_ai.views.code_generation_chat import CodeGenerationChat
urlpatterns = [
    path('project-overview/', ProjectOverview.as_view(), name='project-overview'),
    path('project-files/', ProjectFilesView.as_view(), name='project-files'),
    path('project-structure/', ProjectStructure.as_view(), name='project-structure'),
    path('project-model-fields/', ProjectModelFields.as_view(), name='project-model-fields'),
    path('project-functionalities/', ProjectFunctionalities.as_view(), name='project-functionalities'),
    path('project-business-logic/', ProjectBusinessLogic.as_view(), name='project-business-logic'),
    path('project-files-download/', ProjectFileDownload.as_view(), name='project-files-donwload'),
    path('project-code/', ProjectCode.as_view(), name='project-code'),
    path('project-code-file/', ProjectCodeFile.as_view(), name='project-code-file'),
    path('run-test/', RunTest.as_view(), name='run-test'),
    path('run-migrations/', RunMigrations.as_view(), name='run-migrations'),
    path('code-generation-chat/', CodeGenerationChat.as_view(), name='code-generation-chat'),
    path('approval/', CodeGenerationChat.as_view(), name='code-generation-chat'),
]