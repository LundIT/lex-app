from django.db import models
from django_lifecycle import LifecycleModel

from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction


class UserChangeLog(LifecycleModel):
    """
    A model to log changes made by users.

    Attributes
    ----------
    modification_restriction : AdminReportsModificationRestriction
        Restriction applied to modifications.
    id : AutoField
        Primary key for the log entry.
    user_name : TextField
        Name of the user who made the change.
    timestamp : DateTimeField
        Time when the change was made.
    message : TextField
        Message describing the change.
    traceback : TextField, optional
        Traceback information if available, default is an empty string.
    calculationId : TextField
        ID of the calculation, default is '-1'.
    calculation_record : TextField
        Record of the calculation, default is 'legacy'.
    """
    modification_restriction = AdminReportsModificationRestriction()
    id = models.AutoField(primary_key=True)
    user_name = models.TextField()
    timestamp = models.DateTimeField()
    message = models.TextField()
    traceback = models.TextField(default="", null=True)
    calculationId = models.TextField(default='-1')
    calculation_record = models.TextField(default="legacy")

    class Meta:
        app_label = 'lex_app'

    def save(self, *args, **kwargs):
        """
        Save the UserChangeLog instance.

        If the instance is new (id is None), it calls the parent class's save method.

        Parameters
        ----------
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        if self.id is None:
            super(UserChangeLog, self).save(*args, **kwargs)
    #
    # @hook(AFTER_SAVE, on_commit=True)
    # def create_user_change_log(self):
    #     builder = LexLogger().builder() \
    #         .add_heading("User Change Log", level=2) \
    #         .add_paragraph(f"**User Name:** {self.user_name}") \
    #         .add_paragraph(f"**Timestamp:** {self.timestamp}") \
    #         .add_paragraph(f"**Message:** {self.message}") \
    #         .add_paragraph(f"**Calculation ID:** {self.calculationId}") \
    #         .add_paragraph(f"**Calculation Record:** {self.calculation_record}")
    #     # Optionally add a traceback if available
    #     if self.traceback:
    #         builder.add_heading("Traceback", level=3)
    #         builder.add_code_block(self.traceback)
    #
    #     builder.log(class_name="UserChangeLog")
