from django_lifecycle import LifecycleModel, hook, BEFORE_UPDATE, AFTER_UPDATE
from django_lifecycle.conditions import WhenFieldValueChangesTo, WhenFieldHasChanged, WhenFieldValueWas, WhenFieldValueIs, WhenFieldValueWasNot, WhenFieldValueIsNot
from lex.lex_app.lex_models.LexModel import LexModel
from lex.lex_app.rest_api.signals import update_calculation_status
from django.db import models


class CalculateField(models.BooleanField):
    pass

class CalculationModel(LexModel):

    IN_PROGRESS = 'IN_PROGRESS'
    ERROR = 'ERROR'
    ABORTED = 'ABORTED'
    SUCCESS = 'SUCCESS'
    NOT_CALCULATED = 'NOT_CALCULATED'

    STATUSES = [
        (IN_PROGRESS, 'IN_PROGRESS'),
        (ERROR, 'ERROR'),
        (SUCCESS, 'SUCCESS'),
        (NOT_CALCULATED, 'NOT_CALCULATED'),
        (ABORTED, 'ABORTED'),
    ]

    is_calculated =  models.CharField(max_length=50, choices=STATUSES, default=NOT_CALCULATED)
    calculate = CalculateField(default=False)

    class Meta:
        abstract = True

    @hook(AFTER_UPDATE)
    def after_calculate(self):
        try:
            self.update()
            self.is_calculated = self.SUCCESS
            self.save(skip_hooks=True)
            update_calculation_status(self)
        except Exception as e:
            self.is_calculated = self.ERROR
            self.save(skip_hooks=True)
            update_calculation_status(self)
            raise e

    # @hook(AFTER_UPDATE, condition=(WhenFieldValueIsNot('is_calculated', 'IN_PROGRESS') &
    #                                WhenFieldValueWasNot('is_calculated', 'NOT_CALCULATED')))
    # def after_calculate2(self):
    #     self.is_calculated = self.NOT_CALCULATED
    #     self.save(skip_hooks=True)
    #
    # @hook(AFTER_UPDATE, condition=(WhenFieldValueChangesTo('is_calculated', 'SUCCESS') |
    #                                WhenFieldValueChangesTo('is_calculated', 'ERROR')))
    # def after_calculate2(self):
    #     print(self)
    #     update_calculation_status(self)