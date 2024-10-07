from django.apps import AppConfig


class ReactConfig(AppConfig):
    """
    Configuration for the 'react' application.

    Attributes
    ----------
    default_auto_field : str
        Specifies the type of auto-created primary key field.
    name : str
        The name of the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'react'
