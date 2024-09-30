from django.apps import AppConfig


class ReactConfig(AppConfig):
    """
    Configuration for the React application.

    This class sets the default auto field and the name for the Django app.

    Attributes
    ----------
    default_auto_field : str
        The type of auto field to use for primary keys.
    name : str
        The name of the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'react'
