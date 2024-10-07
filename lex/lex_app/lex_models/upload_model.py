import os
from functools import wraps

from celery import shared_task, Task
from celery.app.control import Control
from celery.signals import task_postrun
from django.db.models import Model, BooleanField

from lex.lex_app.logging.CalculationIDs import CalculationIDs
from lex.lex_app.rest_api.context import context_id
from lex.lex_app.rest_api.signals import update_calculation_status


def custom_shared_task(function):
    """
    Custom shared task decorator.

    Wraps a function to be a shared task with a callback.

    Parameters
    ----------
    function : callable
        The function to be wrapped as a shared task.

    Returns
    -------
    callable
        The wrapped function.
    """
    @shared_task(base=CallbackTask)
    @wraps(function)
    def wrap(*args, **kwargs):
        return_value = (function(*args, **kwargs), args)
        return return_value

    return wrap

##################
# CELERY SIGNALS #
##################
@task_postrun.connect
def task_done(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """
    Signal handler for task postrun.

    Shuts down the Celery worker after task completion.

    Parameters
    ----------
    sender : type, optional
        The sender of the signal.
    task_id : str, optional
        Unique id of the executed task.
    task : Task, optional
        The executed task instance.
    args : tuple, optional
        Original arguments for the executed task.
    kwargs : dict, optional
        Original keyword arguments for the executed task.
    **kw : dict
        Additional keyword arguments.
    """
    control = Control(app=task.app)
    control.shutdown()

class CallbackTask(Task):
    """
    Custom Celery Task with callbacks for success and failure.
    """
    def on_success(self, retval, task_id, args, kwargs):
        """
        Called when a task succeeds.

        Parameters
        ----------
        retval : any
            The return value of the task.
        task_id : str
            Unique id of the executed task.
        args : tuple
            Original arguments for the executed task.
        kwargs : dict
            Original keyword arguments for the executed task.
        """
        if self.name != "initial_data_upload":
            record = retval[1][0]
            record.is_calculated = True
            record.calculate = False
            record.save()
            update_calculation_status(self)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called when a task fails.

        Parameters
        ----------
        exc : Exception
            The exception raised by the task.
        task_id : str
            Unique id of the failed task.
        args : tuple
            Original arguments for the task that failed.
        kwargs : dict
            Original keyword arguments for the task that failed.
        einfo : ExceptionInfo
            Exception information.
        """
        if self.name != "initial_data_upload":
            record = args[0]
            record.is_calculated = False
            record.calculate = False
            record.dont_update = True
            record.save()
            record.dont_update = False
            update_calculation_status(record)

class UploadModelMixin(Model):
    """
    Mixin for upload models.

    This mixin provides common functionality for models that handle uploads.
    """

    class Meta():
        abstract = True
        # app_label = "ACP_PFE"

        

    def update(self):
        """
        Update the model instance.

        This method should be overridden by subclasses to provide custom update logic.
        """
        pass


class IsCalculatedField(BooleanField):
    """
    Custom BooleanField to indicate if a calculation is completed.
    """
    pass

class CalculateField(BooleanField):
    """
    Custom BooleanField to indicate if a calculation should be performed.
    """
    pass

class ConditionalUpdateMixin(Model):
    """
    Mixin for conditional updates in models.

    This mixin provides functionality to conditionally perform calculations and update the model.
    """

    celery_result = None
    class Meta():
        abstract = True

    is_calculated = IsCalculatedField(default=False)
    calculate = CalculateField(default=False)

    @staticmethod
    def conditional_calculation(function):
        """
        Decorator to conditionally perform a calculation.

        Parameters
        ----------
        function : callable
            The function to be conditionally executed.

        Returns
        -------
        callable
            The wrapped function.
        """
        def wrap(*args, **kwargs):
            """
            Wrapper function to handle conditional calculation.

            Parameters
            ----------
            *args : tuple
                Positional arguments for the function.
            **kwargs : dict
                Keyword arguments for the function.

            Returns
            -------
            any
                The return value of the function or None.
            """
            self = args[0]

            if getattr(self, 'dont_update', False):
                return None

            if not self.calculate:
                self.is_calculated = False
                self.dont_update = True
                self.save()
                self.dont_update = False
                return None

            try:
                self.is_calculated = False
                self.dont_update = True
                self.save()

                if (hasattr(function, 'delay') and
                    os.getenv("DEPLOYMENT_ENVIRONMENT")
                        and os.getenv("ARCHITECTURE") == "MQ/Worker"):
                    obj = CalculationIDs.objects.filter(context_id=context_id.get()['context_id']).first()
                    calculation_id = getattr(obj, "calculation_id", "test_id")
                    return_value = function.apply_async(args=args, kwargs=kwargs, task_id=str(calculation_id))
                    self.celery_result = return_value
                else:
                    return_value = function(*args, **kwargs)
                    if (not hasattr(self, 'is_inner_calculation') or
                            not self.is_inner_calculation):
                        self.is_calculated = True
                        self.calculate = False
                        self.dont_update = True
                        self.save()
                        self.dont_update = False
                        update_calculation_status(self)

                return return_value
            except Exception as e:
                self.is_calculated = False
                self.calculate = False
                self.dont_update = True
                self.save()
                self.dont_update = False
                update_calculation_status(self)
                raise e

        return wrap
