import json
from io import BytesIO

import pandas as pd
from django.http import FileResponse
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey

from lex.lex_app.rest_api.generic_filters import UserReadRestrictionFilterBackend, ForeignKeyFilterBackend
# from lex.lex_app.rest_api.model_collection.model_collection import get_relation_fields
from lex.lex_app.rest_api.views.model_entries.filter_backends import PrimaryKeyListFilterBackend
from lex_app.rest_api.model_collection.utils import get_relation_fields


class ModelExportView(GenericAPIView):
    """
    A view for exporting model data to an Excel file.

    This view handles POST requests to export data from a specified model
    container to an Excel file. The data can be filtered based on user
    permissions and specified filters.

    Attributes
    ----------
    filter_backends : list
        List of filter backends to be applied to the queryset.
    model_collection : None
        Placeholder for the model collection.
    http_method_names : list
        List of allowed HTTP methods.
    permission_classes : list
        List of permission classes to be applied to the view.
    """
    filter_backends = [UserReadRestrictionFilterBackend, PrimaryKeyListFilterBackend, ForeignKeyFilterBackend]
    model_collection = None
    http_method_names = ['post']
    permission_classes = [HasAPIKey | IsAuthenticated]



    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to export model data.

        This method processes the request to export data from the specified
        model container. It applies necessary filters, converts the data to
        a DataFrame, and writes it to an Excel file.

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
        FileResponse
            A response containing the generated Excel file.
        """
        model_container = kwargs['model_container']
        model = model_container.model_class
        queryset = ForeignKeyFilterBackend().filter_queryset(request, model.objects.all(), None)
        queryset = UserReadRestrictionFilterBackend()._filter_queryset(request, queryset, model_container)
        json_data = json.loads(str(request.body, encoding='utf-8'))
        if json_data["filtered_export"] is not None:
            queryset = PrimaryKeyListFilterBackend().filter_for_export(json_data, queryset, self)

        df = pd.DataFrame.from_records(queryset.values())
        relationfields = get_relation_fields(model)

        for field in relationfields:
            fieldName = field.attname
            fieldObjects = field.remote_field.model.objects.all()
            fieldObjectsDict = {v.pk: str(v) for v in fieldObjects}
            df[fieldName] = df[fieldName].map(fieldObjectsDict)

        excel_file = BytesIO()
        writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')

        df.to_excel(writer, sheet_name=model.__name__, merge_cells=False, freeze_panes=(1, 1), index=True)

        writer.save()
        writer.close()
        excel_file.seek(0)

        return FileResponse(excel_file)