from django.db.models import TextField


class BokehField(TextField):
    """
    A custom Django model field that extends TextField with a predefined max_length.

    Attributes
    ----------
    max_length : int
        The maximum length of the text field, set to 1000 characters.
    """
    max_length = 1000
    pass