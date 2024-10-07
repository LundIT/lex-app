from abc import abstractmethod

from django.db import models
from django.db import transaction
from django_lifecycle import hook, AFTER_UPDATE, AFTER_CREATE

from lex.lex_app.lex_models.LexModel import LexModel
from lex.lex_app.rest_api.signals import update_calculation_status


class CalculationModel(LexModel):
    """
    Abstract base class for calculation models.

    Attributes
    ----------
    IN_PROGRESS : str
        Status indicating the calculation is in progress.
    ERROR : str
        Status indicating an error occurred during calculation.
    SUCCESS : str
        Status indicating the calculation was successful.
    NOT_CALCULATED : str
        Status indicating the calculation has not been performed.
    ABORTED : str
        Status indicating the calculation was aborted.
    STATUSES : list of tuple
        List of status choices for the `is_calculated` field.
    is_calculated : models.CharField
        Field to store the calculation status.
    """

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

    is_calculated =  models.CharField(max_length=50, choices=STATUSES, default=NOT_CALCULATED)

    class Meta:
        abstract = True

    @abstractmethod
    def calculate(self):
        """
        Abstract method to perform the calculation.

        This method should be implemented by subclasses.
        """
        pass
    
    # TODO: For the Celery task cases, this hook should be updated
    
    @hook(AFTER_UPDATE, on_commit=True)
    @hook(AFTER_CREATE, on_commit=True)
    def calculate_hook(self):
        """
        Hook method to perform calculation after model update or creation.

        This method is triggered after the model instance is updated or created.
        It handles the calculation process and updates the `is_calculated` status.

        Raises
        ------
        Exception
            If an error occurs during the calculation.
        """
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

