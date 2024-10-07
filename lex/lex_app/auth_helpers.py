import os
import requests
from keycloak.keycloak_openid import KeycloakOpenID
from django.contrib.auth.models import User, Group
from sentry_sdk import set_user

ADMIN = 'admin'
STANDARD = 'standard'
VIEW_ONLY = 'view-only'

def get_tokens_and_permissions(request):
    """
    Retrieve tokens and permissions for the given request.

    This function interacts with Keycloak to exchange the provided access token
    for a confidential access token and fetches the user's permissions.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object containing the authorization header.

    Returns
    -------
    dict
        A dictionary containing the access token, confidential access token,
        user roles, permissions, and the token response.
    """
    access_token = request.headers["Authorization"].split("Bearer ")[-1]

    keycloak_url = f"{os.getenv('KEYCLOAK_URL')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "client_id": os.getenv('KEYCLOAK_CLIENT_ID'),
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": access_token,
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": os.getenv('KEYCLOAK_CONFIDENTIAL_CLIENT_ID', 'LEX_LOCAL_ENV_CONFIDENTIAL')
    }

    response = requests.post(keycloak_url, headers=headers, data=data)
    print(response.json())
    confidential_access_token = response.json()["access_token"]

    keycloak_openid = KeycloakOpenID(server_url=os.getenv('KEYCLOAK_URL') + "/",
                                     realm_name=os.getenv('KEYCLOAK_REALM'),
                                     client_id=os.getenv('KEYCLOAK_CONFIDENTIAL_CLIENT_ID', 'LEX_LOCAL_ENV_CONFIDENTIAL'),
                                     client_secret_key=os.getenv('KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET', '6jriqnnNsKPoJgzXOAU9TbwVwAkVlDJn'),
                                     verify=True)
    for item in keycloak_openid.uma_permissions(token=confidential_access_token):
        print(item)
    permissions = {item['rsid']: item.get('scopes', []) for item in
                   keycloak_openid.uma_permissions(token=confidential_access_token)}
    print(request.user.__dict__)
    return {
            "access_token": access_token,
            "confidential_access_token": confidential_access_token,
            "roles": request.user.roles,
            "permissions": permissions,
            "token": response.json()}

def get_user_info(request):
    """
    Retrieve user information and permissions for the given request.

    This function fetches the user's name, email, roles, and permissions.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object containing the user information.

    Returns
    -------
    dict
        A dictionary containing the user's name, email, roles, and permissions.
    """
    return {"user":
                {
                    "name": request.user.name,
                    "email": request.user.email
                 },
            "roles": request.user.roles,
            "permissions": get_tokens_and_permissions(request)["permissions"]}


def resolve_user(request, id_token, rbac=True):
    """
    Resolve and update user information based on the provided ID token.

    This function sets the user in Sentry, creates or updates the user in the
    Django User model, and assigns the user to appropriate groups based on roles.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object.
    id_token : dict
        The ID token containing user information.
    rbac : bool, optional
        Flag to determine if role-based access control (RBAC) should be applied (default is True).

    Returns
    -------
    User or None
        The resolved user object or None if the user does not have the required roles.
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
