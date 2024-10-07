from django.db.models import Model, TextField

from lex.lex_app.rest_api.views.model_entries import One


class CreatedByMixin(Model):
    """
    A Django model mixin that adds a 'created_by' field to the model.

    This mixin automatically sets the 'created_by' field to the current user's name
    when the model instance is saved.

    Attributes
    ----------
    created_by : TextField
        A text field to store the name of the user who created the model instance.

    Methods
    -------
    save(*args, **kwargs)
        Overrides the save method to set the 'created_by' field before saving.
    """
    created_by = TextField(max_length=255, editable=False, default="", null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.created_by = One.user_name
        super().save(*args, **kwargs)

