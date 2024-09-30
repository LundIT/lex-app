from django.contrib.auth.models import User, Group
from sentry_sdk import set_user

ADMIN = 'admin'
STANDARD = 'standard'
VIEW_ONLY = 'view-only'


def resolve_user(request, id_token, rbac=True):
    """
    Resolve a user from the given request and ID token.

    This function interacts with the Django User model to either get or create a user
    based on the provided ID token. It also sets the user's email, name, and roles.
    If RBAC (Role-Based Access Control) is enabled, it assigns the user to the appropriate
    Django groups based on the roles provided in the ID token.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object.
    id_token : dict
        The ID token containing user information.
    rbac : bool, optional
        Flag to enable or disable Role-Based Access Control (default is True).

    Returns
    -------
    User or None
        The resolved user object, or None if the user does not have the required roles.
    """
    # ask graph if logged in user is in a group /me/memberOf
    # want to see group 6d558e06-309d-4d6c-bb50-54f37a962e40
    # in http://graph.microsoft.com/v1.0/me/memberOf
    # in request._request.headers._store['authorization'] is auth header
    set_user({"name": id_token['name'], "email": id_token['email']})
    user, _ = User.objects.get_or_create(username=id_token['sub'])
    user.email = id_token['email']
    user.name = id_token['name'] if id_token['name'] in id_token.values() else "unknown"
    user.roles = []
    if rbac:
        user_roles = id_token['client_roles']
        user.roles = user_roles
        user.save()

        if all(item not in user_roles for item in [ADMIN, STANDARD, VIEW_ONLY]):
            return None

        # Create or get existing groups
        admin_group, created = Group.objects.get_or_create(name=ADMIN)
        standard_group, created = Group.objects.get_or_create(name=STANDARD)
        view_only_group, created = Group.objects.get_or_create(name=VIEW_ONLY)

        # Assign user to django groups according to KeyCloak data
        if ADMIN in user_roles and admin_group not in user.groups.all():
            user.groups.add(admin_group)
        if STANDARD in user_roles and standard_group not in user.groups.all():
            user.groups.add(standard_group)
        if VIEW_ONLY in user_roles and view_only_group not in user.groups.all():
            user.groups.add(view_only_group)
    user.save()

    return user

# Below part is needed when the Memcached cache framework is used
# to save OIDC related key/value pairs

# from django.utils.encoding import smart_str
#
# def _smart_key(key):
#     return smart_str(''.join([c for c in str(key) if ord(c) > 32 and ord(c) != 127]))
#
# def make_key(key, key_prefix, version):
#     "Truncate all keys to 250 or less and remove control characters"
#     return ':'.join([key_prefix, str(version), _smart_key(key)])[:250]
