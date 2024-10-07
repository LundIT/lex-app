from django.db.models import FileField


class PDFField(FileField):
    """
    A custom Django model field for handling PDF files.

    This field extends the FileField to provide additional functionality
    specific to PDF files.

    Attributes
    ----------
    max_length : int
        The maximum length of the file name. Default is 300.
    """
    max_length = 300
    pass