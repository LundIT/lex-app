from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_lifecycle import hook, AFTER_SAVE

from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction
from django.db import models


class CalculationIDs(models.Model):
    modification_restriction = AdminReportsModificationRestriction()
    id = models.AutoField(primary_key=True)
    context_id = models.TextField(default='test_id')
    calculation_record = models.TextField()
    calculation_id = models.TextField(default='test_id')

    class Meta:
        app_label = 'lex_app'


    @hook(AFTER_SAVE)
    def calculation_ids(self):
        channel_layer = get_channel_layer()

        calculation_record = self.calculation_record
        calculation_id = self.calculation_id
        context_id = self.context_id

        message = {
            'type': 'calculation_id',
            'payload': {
                'calculation_record': calculation_record,
                'calculation_id': calculation_id,
                'context_id': context_id
            }
        }
        async_to_sync(channel_layer.group_send)("calculations", message)
