import json

from rest_framework import filters


# TODO: test this
class UserReadRestrictionFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that restricts user read access based on model-specific rules.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset based on user read restrictions.
    _filter_queryset(request, queryset, model_container)
        Helper method to apply the read restrictions.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset based on user read restrictions.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model_container = view.kwargs['model_container']
        return self._filter_queryset(request, queryset, model_container)

    def _filter_queryset(self, request, queryset, model_container):
        """
        Helper method to apply the read restrictions.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        model_container : ModelContainer
            The container holding the model class.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model = model_container.model_class
        if hasattr(model, 'modification_restriction'):
            pks = [obj.pk for obj in queryset if model.modification_restriction.can_be_read(instance=obj, user=request.user, violations=[])]
            queryset.filter(pk__in=pks)
        return queryset


def create_filter_queries_from_tree_paths(all_filter_queries, filter_node, query_string_so_far):
    """
    Recursively creates filter queries from a tree structure.

    Parameters
    ----------
    all_filter_queries : dict
        The dictionary to store the filter queries.
    filter_node : dict
        The current node in the filter tree.
    query_string_so_far : str
        The query string constructed so far.
    """
    if 'entries' in filter_node:
        all_filter_queries[query_string_so_far + 'in'] = filter_node['entries']
    else:
        for key, value in filter_node['children'].items():
            new_query_string = query_string_so_far + key + '__'
            create_filter_queries_from_tree_paths(all_filter_queries, value, new_query_string)


class ForeignKeyFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that filters querysets based on foreign key relationships.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset based on foreign key relationships.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset based on foreign key relationships.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        active_filter_tree = request.GET.get('activeFilterTree', None)
        all_filter_queries = {}
        if active_filter_tree is not None:
            active_filter_tree = json.loads(active_filter_tree)
            create_filter_queries_from_tree_paths(all_filter_queries, active_filter_tree, '')
        return queryset.filter(**all_filter_queries)


class PrimaryKeyListFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that filters querysets based on a list of primary keys.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset based on a list of primary keys.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset based on a list of primary keys.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        model_container = view.kwargs['model_container']
        filter_arguments = {
            model_container.pk_name + '__in':
                list(filter(lambda x: x != '', request.query_params.dict()['pks'].split(',')))
        } if 'pks' in request.query_params.dict() else {}
        return queryset.filter(**filter_arguments)


class StringFilterBackend(filters.BaseFilterBackend):
    """
    A filter backend that filters querysets based on string parameters.

    Methods
    -------
    filter_queryset(request, queryset, view)
        Filters the queryset based on string parameters.
    """
    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset based on string parameters.

        Parameters
        ----------
        request : HttpRequest
            The HTTP request object.
        queryset : QuerySet
            The initial queryset to be filtered.
        view : View
            The view instance.

        Returns
        -------
        QuerySet
            The filtered queryset.
        """
        filter_arguments = request.GET.get('searchParams', '{}')
        return queryset.filter(**json.loads(filter_arguments))