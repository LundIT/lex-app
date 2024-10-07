from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that extends PageNumberPagination.

    This class allows the client to set the page size using a query parameter.

    Attributes
    ----------
    page_size_query_param : str
        The name of the query parameter for setting the page size.
    """
    page_size_query_param = 'size'


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    Custom pagination class that extends LimitOffsetPagination.

    This class allows the client to set the limit and offset using query parameters.

    Attributes
    ----------
    limit_query_param : str
        The name of the query parameter for setting the limit.
    offset_query_param : str
        The name of the query parameter for setting the offset.
    """
    limit_query_param = 'limit'
    offset_query_param = 'offset'
