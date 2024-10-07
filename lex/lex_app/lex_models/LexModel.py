from django.db import models
from django_lifecycle import LifecycleModel, hook, AFTER_UPDATE, AFTER_CREATE

from lex.lex_app.rest_api.context import context_id


class LexModel(LifecycleModel):
    """
    Abstract base model that automatically updates 'created_by' and 'edited_by' fields.

    Attributes
    ----------
    created_by : models.TextField
        Field to store the creator's information.
    edited_by : models.TextField
        Field to store the editor's information.
    """
    
    created_by = models.TextField(null=True, blank=True, editable=False)
    edited_by = models.TextField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True

    @hook(AFTER_UPDATE)
    def update_edited_by(self):
        """
        Hook to update the 'edited_by' field after the model is updated.

        This method retrieves the current context and updates the 'edited_by' field
        with the name and sub of the authenticated user, if available. Otherwise,
        it sets the field to 'Initial Data Upload'.
        """
        context = context_id.get()
        if context and hasattr(context['request_obj'], 'auth'):
            self.edited_by = f"{context['request_obj'].auth['name']} ({context['request_obj'].auth['sub']})"
        else:
            self.edited_by = 'Initial Data Upload'

    @hook(AFTER_CREATE)
    def update_created_by(self):
        """
        Hook to update the 'created_by' field after the model is created.

        This method retrieves the current context and updates the 'created_by' field
        with the name and sub of the authenticated user, if available. Otherwise,
        it sets the field to 'Initial Data Upload'.
        """
        context = context_id.get()
        if context and hasattr(context['request_obj'], 'auth'):
            self.created_by = f"{context['request_obj'].auth['name']} ({context['request_obj'].auth['sub']})"
        else:
            self.created_by = 'Initial Data Upload'