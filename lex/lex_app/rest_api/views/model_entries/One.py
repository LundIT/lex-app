import traceback
from datetime import datetime

from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin

from lex.lex_app.rest_api.context import OperationContext
from lex.lex_app.rest_api.views.model_entries.mixins.DestroyOneWithPayloadMixin import DestroyOneWithPayloadMixin
from lex.lex_app.rest_api.views.model_entries.mixins.ModelEntryProviderMixin import ModelEntryProviderMixin
from lex.lex_app.rest_api.views.utils import get_user_name, get_user_email

user_name = None
user_email = None


class OneModelEntry(ModelEntryProviderMixin, DestroyOneWithPayloadMixin, RetrieveUpdateDestroyAPIView, CreateAPIView):

    def create(self, request, *args, **kwargs):
        from lex.lex_app.logging.UserChangeLog import UserChangeLog
        model_container = self.kwargs['model_container']

        calculationId = self.kwargs['calculationId']

        with OperationContext(request) as context_id:

            # user_change_log = UserChangeLog(calculationId=calculationId, calculation_record=f"{model_container.id}", message=f"Update of a {model_container.id} started", timestamp=datetime.now(), user_name=get_user_name(request))
            # user_change_log.save()
            user_name = get_user_name(request)
            user_email = get_user_email(request)
            try:
                with transaction.atomic():
                    response = CreateModelMixin.create(self, request, *args, **kwargs)
            except Exception as e:
                # user_change_log = UserChangeLog(calculationId=calculationId,
                #                                 calculation_record=f"{model_container.id}",
                #                                 message=f"{e}",
                #                                 timestamp=datetime.now(), user_name=get_user_name(request), traceback=traceback.format_exc())
                # user_change_log.save()
                raise APIException({"error": f"{e} ", "traceback": traceback.format_exc()})

            # user_change_log = UserChangeLog(calculationId=calculationId, calculation_record=f"{model_container.id}", message=f'Creation of {model_container.id} with id {response.data["id"]} successful',
            #                                 timestamp=datetime.now(), user_name=get_user_name(request))
            # user_change_log.save()
            #
            return response

    def update(self, request, *args, **kwargs):
        from lex.lex_app.logging.UserChangeLog import UserChangeLog
        from lex.lex_app.logging.CalculationIDs import CalculationIDs

        model_container = self.kwargs['model_container']
        calculationId = self.kwargs['calculationId']

        with OperationContext(request) as context_id:

            if "calculate" in request.data and request.data["calculate"] == "true":
                CalculationIDs.objects.update_or_create(calculation_record=f"{model_container.id}_{self.kwargs['pk']}",
                                                        context_id=context_id['context_id'],
                                                        defaults={'calculation_id': calculationId})

            if "edited_file" not in request.data:
                user_change_log = UserChangeLog(calculationId=calculationId,
                                                message=f"Update of a {model_container.id} started",
                                                timestamp=datetime.now(),
                                                user_name=get_user_name(request))
                user_change_log.save()

            try:
                response = UpdateModelMixin.update(self, request, *args, **kwargs)

            except Exception as e:
                user_change_log = UserChangeLog(calculationId=calculationId, message=f"{e}",
                                                timestamp=datetime.now(), user_name=get_user_name(request),
                                                traceback=traceback.format_exc())
                user_change_log.save()

                raise APIException({"error": f"{e} ", "traceback": traceback.format_exc()})

            if "edited_file" in request.data:
                user_change_log = UserChangeLog(calculationId=calculationId,
                                                message=f'{request.data["edited_file"]} file is opened for editing in class {model_container.id} and record {response.data["id"]}',
                                                timestamp=datetime.now(), user_name=get_user_name(request))
            else:
                user_change_log = UserChangeLog(calculationId=calculationId,
                                                message=f'Update of {model_container.id} with id {response.data["id"]} successful',
                                                timestamp=datetime.now(), user_name=get_user_name(request))
            user_change_log.save()
            return response
