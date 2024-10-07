from django.apps import AppConfig


class ReactConfig(AppConfig):
    """
    Configuration for the React application.

    Attributes
    ----------
    default_auto_field : str
        The default type of auto field to use for models in this app.
    name : str
        The name of the application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'react'
