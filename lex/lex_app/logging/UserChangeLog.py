from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction
from django.db import models

from lex_app.logging.LogModel import LogModel


class UserChangeLog(LogModel):
    calculationId = models.TextField(default='-1')
    user_name = models.TextField()
    traceback = models.TextField(default="", null=True)


    class Meta:
        app_label = 'lex_app'

    def save(self, *args, **kwargs):
        if self.id is None:
            super(UserChangeLog, self).save(*args, **kwargs)