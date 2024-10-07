from django.db.models import ForeignKey, IntegerField, FloatField, BooleanField, DateField, DateTimeField, FileField, \
    ImageField, AutoField, JSONField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from lex.lex_app.rest_api.fields.Bokeh_field import BokehField
from lex.lex_app.rest_api.fields.HTML_field import HTMLField
from lex.lex_app.rest_api.fields.PDF_field import PDFField
from lex.lex_app.rest_api.fields.XLSX_field import XLSXField
from lex.lex_app.rest_api.views.permissions.UserPermission import UserPermission

DJANGO_FIELD2TYPE_NAME = {
    ForeignKey: 'foreign_key',
    IntegerField: 'int',
    FloatField: 'float',
    BooleanField: 'boolean',
    DateField: 'date',
    DateTimeField: 'date_time',
    FileField: 'file',
    PDFField: 'pdf_file',
    XLSXField: 'xlsx_file',
    HTMLField: 'html',
    BokehField: 'bokeh',
    ImageField: 'image_file',
    JSONField: 'json'
}

DEFAULT_TYPE_NAME = 'string'


def create_field_info(field):
    """
    Create a dictionary containing information about a Django model field.

    Parameters
    ----------
    field : django.db.models.Field
        The Django model field to extract information from.

    Returns
    -------
    dict
        A dictionary containing the field's name, readable name, type, 
        editability, requirement status, default value, and any additional 
        information (e.g., target model for ForeignKey fields).
    """
    default_value = None
    if field.get_default() is not None:
        default_value = field.get_default()

    field_type = type(field)

    additional_info = {}
    if field_type == ForeignKey:
        additional_info['target'] = field.target_field.model._meta.model_name

    return {
        'name': field.name,
        'readable_name': field.verbose_name.title(),
        'type': DJANGO_FIELD2TYPE_NAME.get(field_type, DEFAULT_TYPE_NAME),
        # we assume that auto-fields should not be edited
        'editable': field.editable and not field_type == AutoField,
        'required': not (field.null or default_value),
        'default_value': default_value,
        **additional_info
    }


class Fields(APIView):
    """
    API view to retrieve field information for a given Django model.

    Attributes
    ----------
    http_method_names : list of str
        Allowed HTTP methods for this view.
    permission_classes : list of rest_framework.permissions.BasePermission
        Permissions required to access this view.
    """
    http_method_names = ['get']
    permission_classes = [HasAPIKey | IsAuthenticated, UserPermission]

    def get(self, *args, **kwargs):
        """
        Handle GET requests to retrieve field information.

        Parameters
        ----------
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments, including 'model_container' which 
            contains the model class.

        Returns
        -------
        rest_framework.response.Response
            A response object containing the field information and the 
            primary key field name.
        """
        model = kwargs['model_container'].model_class
        fields = model._meta.fields
        field_info = {'fields': [
            create_field_info(field) for field in fields
        ], 'id_field': model._meta.pk.name}
        # TODO maybe: also send an array containing only those fields that should be presented in the table
        #   to the frontend. This is configured in the model-process-admin-class for the model (which can
        #   be accessed via the model_container) --> The idea is, that the table only shows the main fields
        #   but avoids unnecessary information
        return Response(field_info)
