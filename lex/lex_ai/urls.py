from django.urls import path
from lex_ai.views.project_files import ProjectFilesView

from lex_ai.views.project_overview import ProjectOverview
from lex_ai.views.project_file_download import ProjectFileDownload
from lex_ai.views.project_structure import ProjectStructure
from lex_ai.views.project_functionalities import ProjectFunctionalities
from lex_ai.views.project_business_logic import ProjectBusinessLogic
from lex_ai.views.project_model_fields import ProjectModelFields
from lex_ai.views.project_code import ProjectCode
urlpatterns = [
    path('project-overview/', ProjectOverview.as_view(), name='project-overview'),
    path('project-files/', ProjectFilesView.as_view(), name='project-files'),
    path('project-structure/', ProjectStructure.as_view(), name='project-structure'),
    path('project-model-fields/', ProjectModelFields.as_view(), name='project-model-fields'),
    path('project-functionalities/', ProjectFunctionalities.as_view(), name='project-functionalities'),
    path('project-business-logic/', ProjectBusinessLogic.as_view(), name='project-business-logic'),
    path('project-files-download/', ProjectFileDownload.as_view(), name='project-files-donwload'),
    path('project-code/', ProjectCode.as_view(), name='project-code'),
]