import os
from io import BytesIO

from django.http import FileResponse, JsonResponse
from django_sharepoint_storage.SharePointCloudStorageUtils import get_server_relative_path
from django_sharepoint_storage.SharePointContext import SharePointContext
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


class FileDownloadView(APIView):
    model_collection = None
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated]

    async def main(self, requirement: str):
        from metagpt.roles.di.data_interpreter import DataInterpreter
        from metagpt.utils.recovery_util import save_history


        role = DataInterpreter(max_react_loop=1, tools=["<all>"], react_mode="react")  # integrate the tool
        await role.run(requirement)
        save_history(role=role)

    def get(self, request, *args, **kwargs):
        import asyncio

        # Currently, one of the big problems of the output of this DataIntperpreter is that it translates column names to German
        # while doing the DataFrame opertaions. It can be related to the file name of windpark operators file.

        file_path = "/Users/melihsunbul/LUND_IT/lex-ai/DemoWindparkConsolidation/DemoWindparkConsolidation/Tests/initial_test_files/Windparks.xlsx"
        file_path2 = "/Users/melihsunbul/LUND_IT/lex-ai/DemoWindparkConsolidation/DemoWindparkConsolidation/Tests/initial_test_files/Windparkbetreiber_Übersicht.xlsx"
        requirement = f"""
            You need to upload the Windpark Opertors file to the UploadWindparkOperator table and create the Windpark Operators in WindparkOperator table from the path: {file_path2}.
            You need to upload the Windparks file to the UploadWindparks table and create the Windparks in Windpark table from the path: {file_path}.
            
            
            Follow the below rules:

            1. Analyze and understand the contents of the two excel files you are working with.
            2. Analyze and understand the UploadWinparkOperator, WinparkOperator, UploadWindparks, Windpark and Period models in the DemoWindparkConsolidation application.
            3. Use the lex-app Django application and for the setup of it use lex_app_setup tool without changing anything from it.
            4. DO NOT forget that you will be running in an asynchronous context but Django app operations need to be synchronous. Therefore, do the necessary adjustments for this case when it is needed.
            5. Start the Django Model class's imports with DemoWindparkConsolidation. for example:
                from DemoWindparkConsolidation.UploadFiles.UploadWindparks import UploadWindparks
            6. DO NOT forget to create other Model objects first if they are needed as in a relationship with the relavant models.
            7. DO NOT forget to fill every mandatory field when you create an object from a Model class.
            8. Use CORRECT field names while creating the Model class objects.
        """

        asyncio.run(self.main(requirement))
        return JsonResponse({"download_url": "file_url"})
        # model = kwargs['model_container'].model_class
        # shrp_ctx = SharePointContext()
        # instance = model.objects.filter(pk=request.query_params['pk'])[0]
        # file = instance.__getattribute__(request.query_params['field'])
        # 
        # if os.getenv("KUBERNETES_ENGINE", "NONE") == "NONE":
        #     # TODO, not compatible with production environment
        #     file_url = file.url if not file.url.startswith('/') else file.url
        # else:
        #     file_url = file.url
        # 
        # if os.getenv("STORAGE_TYPE") == "SHAREPOINT":
        #     file = shrp_ctx.ctx.web.get_file_by_server_relative_path(get_server_relative_path(file.url)).execute_query()
        #     binary_file = file.open_binary(shrp_ctx.ctx, get_server_relative_path(file_url))
        #     bytesio_object = BytesIO(binary_file.content)
        #     return FileResponse(bytesio_object)
        # elif os.getenv("STORAGE_TYPE") == "GCS":
        #     return JsonResponse({"download_url": file_url})
        # else:
        #     return FileResponse(open(file_url, 'rb'))