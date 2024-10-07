from django.db.models import Model


class ReportingModelMixin(Model):
    """
    Reporting Models allows the User to download the files as indicated in reporting_fields.

    Attributes
    ----------
    input : bool
        A flag indicating whether the model is in input mode.
    reporting_fields : list
        A list of fields to be included in the report.
    """
    input = False
    reporting_fields = []

    class Meta:
        """
        Meta options for the ReportingModelMixin.

        Attributes
        ----------
        abstract : bool
            Indicates that this is an abstract base class.
        """
        abstract = True
