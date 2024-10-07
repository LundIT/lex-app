import base64
from urllib.parse import parse_qs

from rest_framework import filters


class PrimaryKeyListFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that filters a queryset based on a list of primary key values.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset based on primary key values provided in the request query parameters.
    filter_for_export(json_data, queryset, view)
        Filters the queryset based on primary key values provided in the base64 encoded JSON data.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset based on primary key values provided in the request query parameters.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance that called this filter.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model_container = view.kwargs['model_container']

        if 'ids' in request.query_params.dict():
            ids = {**request.query_params}['ids']
            ids_cleaned = list(filter(lambda x: x != '', ids))
            filter_arguments = {
                f'{model_container.pk_name}__in': ids_cleaned
            }
        else:
            filter_arguments = {}
        return queryset.filter(**filter_arguments)

    def filter_for_export(self, json_data, queryset, view):
        """
        Filters the queryset based on primary key values provided in the base64 encoded JSON data.

        Parameters
        ----------
        json_data : dict
            The JSON data containing the base64 encoded filter parameters.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance that called this filter.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model_container = view.kwargs['model_container']
        decoded = base64.b64decode(json_data["filtered_export"]).decode("utf-8")
        params = parse_qs(decoded)
        if 'ids' in dict(params):
            ids = dict(params)['ids']
            ids_cleaned = list(filter(lambda x: x != '', ids))
            filter_arguments = {
                f'{model_container.pk_name}__in': ids_cleaned
            }
        else:
            filter_arguments = {}
        return queryset.filter(**filter_arguments)


class UserReadRestrictionFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that restricts the queryset based on user read permissions.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset to include only entries that the user has permission to read.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset to include only entries that the user has permission to read.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance that called this filter.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model_container = view.kwargs['model_container']
        user = request.user
        modification_restriction = model_container.get_modification_restriction()

        # Hint: we do not check the general read-permission here, as this is already done by the class UserPermission

        permitted_entry_ids = [entry.id for entry in queryset if
                               modification_restriction.can_be_read(entry, user, None)]
        return queryset.filter(id__in=permitted_entry_ids)
