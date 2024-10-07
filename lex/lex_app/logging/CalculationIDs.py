from django.db import models

from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction


class CalculationIDs(models.Model):
    """
    Model representing calculation IDs with modification restrictions.

    Attributes
    ----------
    modification_restriction : AdminReportsModificationRestriction
        Restriction applied to modifications of the model.
    id : AutoField
        Primary key for the model.
    context_id : TextField
        Context identifier, default is 'test_id'.
    calculation_record : TextField
        Record of the calculation.
    calculation_id : TextField
        Identifier for the calculation, default is 'test_id'.
    """
    modification_restriction = AdminReportsModificationRestriction()
    id = models.AutoField(primary_key=True)
    context_id = models.TextField(default='test_id')
    calculation_record = models.TextField()
    calculation_id = models.TextField(default='test_id')

    class Meta:
        """
        Meta options for the CalculationIDs model.

        Attributes
        ----------
        app_label : str
            Label for the application to which this model belongs.
        """
        app_label = 'lex_app'
