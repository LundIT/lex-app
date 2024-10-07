import traceback
from datetime import datetime

from django.db import transaction
from django.db.models.signals import post_save
from rest_framework.exceptions import APIException
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin

from lex.lex_app.rest_api.views.model_entries.mixins.DestroyOneWithPayloadMixin import DestroyOneWithPayloadMixin
from lex.lex_app.rest_api.views.model_entries.mixins.ModelEntryProviderMixin import ModelEntryProviderMixin
from lex.lex_app.rest_api.views.utils import get_user_name, get_user_email

user_name = None
user_email = None


class CreateOrUpdate(ModelEntryProviderMixin, DestroyOneWithPayloadMixin, RetrieveUpdateDestroyAPIView, CreateAPIView):
    """
    A view that provides default implementations for creating, updating, and destroying model instances.

    This class combines several mixins and generic views to handle the creation or update of a model instance.
    It also logs user changes and handles exceptions during the transaction.

    Methods
    -------
    update(request, *args, **kwargs)
        Handles the update or creation of a model instance, logs the changes, and manages exceptions.
    """
    def update(self, request, *args, **kwargs):
        """
        Handle the update or creation of a model instance.

        This method logs the start of the update, processes the update or creation within a transaction,
        logs any exceptions that occur, and logs the successful completion of the update.

        Parameters
        ----------
        request : Request
            The request object containing the data for the update or creation.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            The response object containing the result of the update or creation.

        Raises
        ------
        APIException
            If an exception occurs during the update or creation process.
        """
        from lex.lex_app.logging.UserChangeLog import UserChangeLog
        from lex.lex_app.lex_models import update_handler
        model_container = self.kwargs['model_container']
        global user_name
        global user_email

        user_change_log = UserChangeLog(message=f"Update of a {model_container.id} started", timestamp=datetime.now(), user_name=get_user_name(request))
        user_change_log.save()
        user_name = get_user_name(request)
        user_email = get_user_email(request)
        instance = model_container.model_class.objects.filter(pk=self.kwargs["pk"]).first()
        try:
            if "next_step" in request.data:
                post_save.disconnect(update_handler)
            with transaction.atomic():
                if instance:
                    response = UpdateModelMixin.update(self, request, *args, **kwargs)
                else:
                    response = CreateModelMixin.create(self, request, *args, **kwargs)
        except Exception as e:
            user_change_log = UserChangeLog(message=f"{e}",
                                            timestamp=datetime.now(), user_name=get_user_name(request), traceback=traceback.format_exc())
            user_change_log.save()

            print(e)
            raise APIException({"error": f"{e} ", "traceback": traceback.format_exc()})

        user_change_log = UserChangeLog(message=f'Update of {model_container.id} with id {response.data["id"]} successful',
                                        timestamp=datetime.now(), user_name=get_user_name(request))
        user_change_log.save()
        post_save.connect(update_handler)
        return response
