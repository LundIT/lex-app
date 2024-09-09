import os
import threading
import traceback
from datetime import datetime

from asgiref.sync import async_to_sync
from celery import current_task
from channels.layers import get_channel_layer
from django_lifecycle import AFTER_SAVE, hook

from lex.lex_app.lex_models.ModificationRestrictedModelExample import AdminReportsModificationRestriction
from lex.lex_app.rest_api.context import context_id
from django.db import models
import inspect
from django.core.cache import cache
from lex.lex_app import settings

from lex.lex_app.logging.CalculationIDs import CalculationIDs
from lex_app.lex_models.LexModel import LexModel
from lex_app.logging.LogModel import LogModel


#### Note: Messages shall be delivered in the following format: "Severity: Message" The colon and the whitespace after are required for the code to work correctly ####
# Severity could be something like 'Error', 'Warning', 'Caution', etc. (See Static variables below!)


class CalculationLog(LogModel):
    calculationId = models.TextField(default='test_id')
    trigger_name = models.TextField(null=True)
    message_type = models.TextField(default="")
    method = models.TextField()
    is_notification = models.BooleanField(default=False)


    # Severities, to be concatenated with message in create statement
    SUCCESS = 'Success: '
    WARNING = 'Warning: '
    ERROR = 'Error: '
    START = 'Start: '
    FINISH = 'Finish: '

    # Message types
    PROGRESS = 'Progress'
    INPUT = 'Input Validation'
    OUTPUT = 'Output Validation'

    class Meta:
        app_label = 'lex_app'

    @hook(AFTER_SAVE, when='is_notification', is_now=True)
    def send_calculation_notification(self):
        channel_layer = get_channel_layer()
        message = {
            'type': 'calculation_notification',  # This is the correct naming convention
            'payload': {
                'id': self.id,
                'message': self.message,
            }
        }
        # notification = Notifications(message=instance.message, timestamp=datetime.now())
        # notification.save()
        async_to_sync(channel_layer.group_send)(f'calculation_notification', message)

    def save(self, *args, **kwargs):
        print(self.calculationId + ": " + self.message)
        if self.id is None:
            super(CalculationLog, self).save(*args, **kwargs)

    @classmethod
    def create(cls, message, message_type="Progress", trigger_name=None, is_notification=False):
        trace_objects = cls.get_trace_objects()["trace_objects"]
        calculation_record = cls.get_trace_objects()["first_model_info"]

        if current_task and os.getenv("CELERY_ACTIVE"):
            obj, created = CalculationIDs.objects.get_or_create(calculation_record=calculation_record if calculation_record else "init_upload",
                                                                calculation_id=str(current_task.request.id),
                                                                defaults={
                                                                    'context_id': getattr(CalculationIDs.objects.filter(calculation_id=str(current_task.request.id)).first(), "context_id", "test_id")})
            calculation_id = getattr(obj, "calculation_id", "test_id")
        else:
            obj, created = CalculationIDs.objects.get_or_create(calculation_record=calculation_record if calculation_record else "init_upload",
                                                                context_id=context_id.get()['context_id'] if context_id.get() else "test_id",
                                                                defaults={
                                                                    'calculation_id': getattr(CalculationIDs.objects.filter(context_id=context_id.get()['context_id']).first(), "calculation_id", "test_id")})
            calculation_id = getattr(obj, "calculation_id", "test_id")

        calc_log = CalculationLog(timestamp=datetime.now(), method=str(trace_objects),
                                  calculation_record=calculation_record if calculation_record else "init_upload", message=message, calculationId=calculation_id,
                                  message_type=message_type,
                                  trigger_name=trigger_name, is_notification=is_notification)
        calc_log.save()

    @classmethod
    def get_calculation_id(cls, calculation_model):
        return f"{str(calculation_model._meta.model_name)}-{str(calculation_model.id)}" if calculation_model is not None else "test_id"

    @classmethod
    def get_trace_objects(cls):
        stack = list(traceback.extract_stack())
        currentframe = inspect.currentframe()
        trace_objects = []
        trace_objects_class_list = []
        first_model_info = None
        i = 0
        while currentframe is not None:
            if 'self' in currentframe.f_locals:
                tempobject = currentframe.f_locals['self']
            else:
                tempobject = None
            filename, methodname, lineno = stack[-(i + 1)].filename, stack[-(i + 1)].name, stack[-(i + 1)].lineno
            i += 1
            currentframe = currentframe.f_back
            if f"{settings.repo_name}" in filename and not "CalculationLog" in filename:
                trimmed_filename = filename.split(os.sep)[-1].split(".")[0]
                if tempobject and hasattr(tempobject, "_meta") and not first_model_info:
                    model_verbose_name = tempobject._meta.model_name
                    record_id = getattr(tempobject, 'id', None)
                    if model_verbose_name and record_id:
                        first_model_info = f"{model_verbose_name}_{record_id}"
                trace_objects.append((trimmed_filename, methodname, lineno, str(tempobject)))
                if hasattr(tempobject, "_meta"):
                    trace_objects_class_list.append(tempobject._meta.model_name)
        trace_objects.reverse()

        result = {
            "trace_objects": trace_objects,
            "first_model_info": first_model_info,
            "trace_objects_class_list": list(set(trace_objects_class_list))
        }

        return result

    @classmethod
    def assertTrue(cls, assertion, message):
        if assertion:
            cls.create(message=message, message_type="Test: Success")
        else:
            cls.create(message=message, message_type="Test: Error")
