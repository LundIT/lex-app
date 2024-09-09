from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_lifecycle import hook, AFTER_SAVE

from lex_app.lex_models.LexModel import LexModel
from lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction
from lex_app.rest_api.signals import get_model_data
from django.db import models


class LogModel(LexModel):
    modification_restriction = AdminReportsModificationRestriction()
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    message = models.TextField()
    calculation_record = models.TextField(default="legacy")
    calculationId = models.TextField(default='')


    class Meta:
        abstract = True

    @hook(AFTER_SAVE)
    def calculation_logs(self):
        channel_layer = get_channel_layer()
        message = {
            'type': 'calculation_log_real_time', # This is the correct naming convention
            'payload': get_model_data(self.calculation_record, self.calculationId)
        }
        async_to_sync(channel_layer.group_send)(f'{self.calculation_record}', message)


