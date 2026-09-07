from django.db.models import FileField


class PDFField(FileField):
    #: See XLSXField.max_length — generated report paths outgrow Django's
    #: FileField default of 100. Passing ``max_length=`` explicitly still wins.
    max_length = 300

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", self.max_length)
        super().__init__(*args, **kwargs)
