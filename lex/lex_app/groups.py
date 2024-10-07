
from django.contrib.auth.models import Group

ADMIN = 'admin'
STANDARD = 'standard'
VIEW_ONLY = 'view-only'


def create_groups():
    """
    Create user groups if they do not already exist.

    This function creates three user groups: 'admin', 'standard', and 'view-only'
    using Django's Group model. If the groups already exist, they will not be created again.

    Returns
    -------
    None
    """
    group1, created = Group.objects.get_or_create(name=ADMIN)
    group2, created = Group.objects.get_or_create(name=STANDARD)
    group3, created = Group.objects.get_or_create(name=VIEW_ONLY)
