import traceback
from datetime import datetime

from lex.lex_app.rest_api.context import OperationContext
from rest_framework.exceptions import APIException
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin

from lex.lex_app.rest_api.views.model_entries.mixins.DestroyOneWithPayloadMixin import DestroyOneWithPayloadMixin
from lex.lex_app.rest_api.views.model_entries.mixins.ModelEntryProviderMixin import ModelEntryProviderMixin
from lex.lex_app.rest_api.views.utils import get_user_name
from django.db import transaction


class OneModelEntry(ModelEntryProviderMixin, DestroyOneWithPayloadMixin, RetrieveUpdateDestroyAPIView, CreateAPIView):

    def create(self, request, *args, **kwargs):
        model_container = self.kwargs['model_container']
        calculationId = self.kwargs['calculationId']

        # Log the start of the operation
        user_log_action = log_user_action(calculationId=calculationId,
                                               model_container=model_container,
                                               message=f"Update of a {model_container.id} started",
                                               request=request)
        user_log_action.save()

        try:
            with transaction.atomic():
                response = CreateModelMixin.create(self, request, *args, **kwargs)
        except Exception as e:
            # Log the exception
            user_log_exception = handle_exception(calculationId=calculationId,
                                                       model_container=model_container,
                                                       request=request,
                                                       exception=e)
            user_log_exception.save()

            raise APIException({"error": f"{e} ", "traceback": traceback.format_exc()})

        # Log the successful creation
        user_log_sucess = log_user_action(calculationId=calculationId,
                                               model_container=model_container,
                                               message=f'Creation of {model_container.id} with id {response.data["id"]} successful',
                                               request=request)
        user_log_sucess.save()

        return response

    def update(self, request, *args, **kwargs):
        from lex.lex_app.logging.CalculationIDs import CalculationIDs

        model_container = self.kwargs['model_container']
        calculationId = self.kwargs['calculationId']

        with OperationContext(request) as context_id:

            # If the request includes calculation trigger, update CalculationIDs
            if "calculate" in request.data and request.data["calculate"] == "true":
                CalculationIDs.objects.update_or_create(calculation_record=f"{model_container.id}_{self.kwargs['pk']}",
                                                        context_id=context_id['context_id'],
                                                        defaults={'calculation_id': calculationId})

            # Log the update of the operation
            if "edited_file" not in request.data:
                user_log_update = log_user_action(calculationId=calculationId,
                                                       model_container=model_container,
                                                       message=f"Update of a {model_container.id} started",
                                                       request=request)
                user_log_update.save()

            instance = model_container.model_class.objects.filter(pk=self.kwargs["pk"]).first()

            # Check if the instance is atomic or not before proceeding with the update
            try:
                if hasattr(instance, 'is_atomic') and not instance.is_atomic:
                    response = UpdateModelMixin.update(self, request, *args, **kwargs)
                else:
                    if "calculate" in request.data and request.data["calculate"] == "true":
                        # post_save.disconnect(update_handler)
                        instance.calculate = True
                        instance.is_calculated = 'IN_PROGRESS'
                        instance.save(skip_hooks=True)
                        # update_calculation_status(instance)

                    # Perfrom the update inside a transaction
                    with transaction.atomic():
                        # post_save.connect(update_handler)
                        response = UpdateModelMixin.update(self, request, *args, **kwargs)

            except Exception as e:
                user_log_exception = handle_exception(calculationId=calculationId,
                                                           model_container=model_container,
                                                           exception=e,
                                                           request=request)

                user_log_exception.save()
                # if not hasattr(instance, 'is_atomic') or instance.is_atomic:
                #     if "calculate" in request.data:
                #         instance.calculate = False
                #         instance.save()
                # print(e)
                raise APIException({"error": f"{e} ", "traceback": traceback.format_exc()})

            # Log the result of the update operation
            log_message = f'{request.data.get("edited_file", "")} file is opened for editing' if "edited_file" in request.data else f'Update of {model_container.id} with id {response.data["id"]} successful'
            user_log_result = log_user_action(calculationId=calculationId,
                                                   model_container=model_container,
                                                   message=log_message,
                                                   request=request)
            user_log_result.save()

            return response


def log_user_action(calculationId, model_container, message, request):
    """Helper method to log user actions for create and update operations."""
    from lex.lex_app.logging.UserChangeLog import UserChangeLog

    user_name = get_user_name(request)

    user_change_log = UserChangeLog(
        calculationId=calculationId,
        calculation_record=f"{model_container.id}",
        message=message,
        timestamp=datetime.now(),
        user_name=user_name,
    )
    return user_change_log


def handle_exception(exception, calculationId, model_container, request):
    from lex.lex_app.logging.UserChangeLog import UserChangeLog

    error_message = traceback.format_exc()
    user_name = get_user_name(request)

    # Log the exception
    user_change_log = UserChangeLog(
        calculationId=calculationId,
        calculation_record=f"{model_container.id}",
        message=str(exception),
        timestamp=datetime.now(),
        user_name=user_name,
        traceback=error_message
    )
    return user_change_log
