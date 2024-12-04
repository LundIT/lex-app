from abc import abstractmethod

from django.db import models
from django.db import transaction
from django_lifecycle import hook, AFTER_UPDATE, AFTER_CREATE

from lex.lex_app.lex_models.LexModel import LexModel
from lex.lex_app.rest_api.signals import update_calculation_status


class CalculationModel(LexModel):

    IN_PROGRESS = 'IN_PROGRESS'
    ERROR = 'ERROR'
    SUCCESS = 'SUCCESS'
    NOT_CALCULATED = 'NOT_CALCULATED'
    ABORTED = 'ABORTED'
    STATUSES = [
        (IN_PROGRESS, 'IN_PROGRESS'),
        (ERROR, 'ERROR'),
        (SUCCESS, 'SUCCESS'),
        (NOT_CALCULATED, 'NOT_CALCULATED'),
        (ABORTED, 'ABORTED')
    ]

    is_calculated = models.CharField(max_length=50, choices=STATUSES, default=NOT_CALCULATED)

    class Meta:
        abstract = True

    @abstractmethod
    def calculate(self):
        pass
    
    # TODO: For the Celery task cases, this hook should be updated
    
    @hook(AFTER_UPDATE, on_commit=True)
    @hook(AFTER_CREATE, on_commit=True)
    def calculate_hook(self):
        try:
            if hasattr(self, 'is_atomic') and not self.is_atomic:
                # TODO: To fix with the correct type
                # update_calculation_status(self)
                self.calculate()
                self.is_calculated = self.SUCCESS
            else:
                with transaction.atomic():
                    self.calculate()
                    self.is_calculated = self.SUCCESS
        except Exception as e:
            self.is_calculated = self.ERROR
            raise e
        finally:
            self.save(skip_hooks=True)
            update_calculation_status(self)

