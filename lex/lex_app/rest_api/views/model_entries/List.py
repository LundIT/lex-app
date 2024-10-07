import traceback

from django.db.models import FloatField, IntegerField, DateField, DateTimeField, TextField, AutoField
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from lex.lex_app.lex_models.upload_model import IsCalculatedField, CalculateField
from lex.lex_app.rest_api.views.model_entries.filter_backends import UserReadRestrictionFilterBackend
from lex.lex_app.rest_api.views.model_entries.mixins.ModelEntryProviderMixin import ModelEntryProviderMixin

INTERVAL_REQUIRING_FIELDS = {FloatField, IntegerField, DateField, DateTimeField}
CALCULATION_FIELDS = {IsCalculatedField, CalculateField}

class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that extends PageNumberPagination.

    This class customizes the pagination behavior by allowing the client to request
    all items by setting the 'perPage' query parameter to -1.

    Attributes
    ----------
    page_query_param : str
        The name of the query parameter for the page number.
    page_size_query_param : str
        The name of the query parameter for the page size.
    """
    page_query_param = 'page'
    page_size_query_param = 'perPage'
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if needed, either returning a page object, or `None` if pagination is not needed.

        Parameters
        ----------
        queryset : QuerySet
            The queryset to paginate.
        request : Request
            The request object.
        view : View, optional
            The view object.

        Returns
        -------
        Page or None
            A page object if pagination is needed, otherwise `None`.
        """
        if request.query_params["perPage"] == -1:
            self.page_size = queryset.count()  # Set the page size equal to the total number of objects in the queryset

        return super().paginate_queryset(queryset, request, view)

class ListModelEntries(ModelEntryProviderMixin, ListAPIView):
    """
    API view to list model entries with custom filtering and pagination.

    This view uses a custom pagination class and several filter backends to provide
    advanced filtering capabilities.

    Attributes
    ----------
    pagination_class : class
        The pagination class to use for this view.
    filter_backends : list
        The list of filter backends to use for this view.
    """
    pagination_class = CustomPageNumberPagination
    # see https://stackoverflow.com/a/40585846
    # We use the UserReadRestrictionFilterBackend for filtering out those instances that the user
    #   does not have access to
    filter_backends = [UserReadRestrictionFilterBackend, DjangoFilterBackend, OrderingFilter]

    def get_lookup_expressions(self, field_type):
        """
        Get the lookup expressions for a given field type.

        Parameters
        ----------
        field_type : type
            The type of the field.

        Returns
        -------
        list of str
            A list of lookup expressions for the field type.
        """
        if field_type in INTERVAL_REQUIRING_FIELDS:
            if field_type in [DateField, DateTimeField]:
                return ['exact', 'lte', 'gte', 'year', 'month', 'day']
            return ['exact', 'lte', 'gte']
        if field_type in [TextField, AutoField]:
            return ['exact', 'icontains']
        return ['exact']

    @property
    def filterset_fields(self):
        """
        Get the filterset fields for the view.

        This method generates a dictionary of fields and their corresponding lookup expressions
        that can be used for filtering.

        Returns
        -------
        dict
            A dictionary where the keys are field names and the values are lists of lookup expressions.

        Raises
        ------
        APIException
            If the filter fields could not be generated.
        """
        # we need to only take those fields where a django-filter exists
        try:
            return_fields = {f.name: self.get_lookup_expressions(type(f)) for f in
                    self.kwargs['model_container'].model_class._meta.fields if (type(f) in FilterSet.FILTER_DEFAULTS or type(f) in CALCULATION_FIELDS)}
            return return_fields
        except Exception as e:
            raise APIException({"error": f"Filter fields could not be generated!", "traceback": traceback.format_exc()})