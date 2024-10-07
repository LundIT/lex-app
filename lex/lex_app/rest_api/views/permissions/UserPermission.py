import inspect

from rest_framework.permissions import BasePermission

READ_METHODS = {'GET'}
CREATE_METHODS = {'POST'}
MODIFY_METHODS = {'PUT', 'PATCH'}
DELETE_METHOD = 'DELETE'


def get_permission_denied_message(access_type, requested_unit, violations):
    """
    Generate a permission denied message.

    Parameters
    ----------
    access_type : str
        The type of access that was denied (e.g., 'read', 'modify').
    requested_unit : str
        The unit that was requested (e.g., 'model', 'instance').
    violations : list of str
        A list of violations that caused the denial.

    Returns
    -------
    str
        A formatted permission denied message.
    """
    details = ''
    if violations:
        details = f' Violations: {", ".join(violations)}'
    return f'You do not have general {access_type}-access to the requested {requested_unit}.{details}'


class UserPermission(BasePermission):
    """
    Permission class to ensure that only certain users can perform specific operations on the data.

    This class checks the user's permissions based on the HTTP method of the request and the
    modification restrictions defined in the model container.

    Attributes
    ----------
    message : str
        The message to be returned when permission is denied.
    """

    message = None

    # TODO: this class can easily extended to also consider permissions set via Django admin

    def has_permission(self, request, view):
        """
        Check if the user has permission to perform the requested action.

        Parameters
        ----------
        request : Request
            The HTTP request object.
        view : View
            The view object.

        Returns
        -------
        bool
            True if the user has permission, False otherwise.
        """
        model_container = view.kwargs['model_container']
        user = request.user
        modification_restriction = model_container.get_modification_restriction()

        if request.method in READ_METHODS:
            violations = []
            if modification_restriction.can_read_in_general(user, violations):
                return True
            self.message = get_permission_denied_message('read', 'model', violations)
            return False

        if request.method in MODIFY_METHODS:
            violations = []
            if modification_restriction.can_modify_in_general(user, violations):
                return True
            self.message = get_permission_denied_message('modify', 'model', violations)
            return False

        if request.method in CREATE_METHODS:
            violations = []
            if modification_restriction.can_create_in_general(user, violations):
                return True
            self.message = get_permission_denied_message('create', 'model', violations)
            return False

        if request.method == DELETE_METHOD:
            violations = []
            if modification_restriction.can_delete_in_general(user, violations):
                return True
            self.message = get_permission_denied_message('delete', 'model', violations)
            return False

        raise ValueError(f'unknow http method {request.method}')

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to perform the requested action on a specific object.

        Parameters
        ----------
        request : Request
            The HTTP request object.
        view : View
            The view object.
        obj : Model
            The object to check permissions against.

        Returns
        -------
        bool
            True if the user has permission, False otherwise.
        """
        model_container = view.kwargs['model_container']
        user = request.user
        modification_restriction = model_container.get_modification_restriction()

        if request.method in READ_METHODS:
            violations = []
            if modification_restriction.can_be_read(obj, user, violations):
                return True
            self.message = get_permission_denied_message('read', 'instance', violations)
            return False

        if request.method in MODIFY_METHODS:
            violations = []
            if 'request_data' in inspect.signature(modification_restriction.can_be_modified).parameters:
                if modification_restriction.can_be_modified(obj, user, violations, request.data):
                    return True
            else:
                if modification_restriction.can_be_modified(obj, user, violations):
                    return True
            self.message = get_permission_denied_message(obj, user, violations)
            return False

        if request.method in CREATE_METHODS:
            return True

        if request.method == DELETE_METHOD:
            violations = []
            if 'request_data' in inspect.signature(modification_restriction.can_be_deleted).parameters:
                if modification_restriction.can_be_deleted(obj, user, violations, request.data):
                    return True
            else:
                if modification_restriction.can_be_deleted(obj, user, violations):
                    return True
            self.message = get_permission_denied_message('delete', 'instance', violations)
            return False

        raise ValueError(f'unknow http method {request.method}')
