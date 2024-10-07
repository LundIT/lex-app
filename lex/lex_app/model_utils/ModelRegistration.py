
import asyncio
import os

import nest_asyncio
from asgiref.sync import sync_to_async


class ModelRegistration:
    """
    A class used to register models, model structures, model styling, and widget structures
    with the process admin site and admin site.
    """
    @classmethod
    def register_models(cls, models):
        """
        Register models with the process admin site and admin site.

        Parameters
        ----------
        models : list
            A list of model classes to be registered.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite, adminSite
        from lex.lex_app.lex_models.Process import Process
        from lex.lex_app.lex_models.html_report import HTMLReport
        from lex.lex_app.lex_models.CalculationModel import CalculationModel

        for model in models:
            if issubclass(model, HTMLReport):
                processAdminSite.registerHTMLReport(model.__name__.lower(), model)
                processAdminSite.register([model])
            elif issubclass(model, Process):
                processAdminSite.registerProcess(model.__name__.lower(), model)
                processAdminSite.register([model])
            elif not issubclass(model, type) and not model._meta.abstract:
                processAdminSite.register([model])
                adminSite.register([model])

                if issubclass(model, CalculationModel):
                    if os.getenv("CALLED_FROM_START_COMMAND"):
                        @sync_to_async
                        def reset_instances_with_aborted_calculations():
                            if not os.getenv("CELERY_ACTIVE"):
                                aborted_calc_instances = model.objects.filter(is_calculated=CalculationModel.IN_PROGRESS)
                                aborted_calc_instances.update(is_calculated=CalculationModel.ABORTED)

                        nest_asyncio.apply()
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(reset_instances_with_aborted_calculations())

    @classmethod
    def register_model_structure(cls, structure: dict):
        """
        Register a model structure with the process admin site.

        Parameters
        ----------
        structure : dict
            A dictionary representing the model structure to be registered.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite
        if structure: processAdminSite.register_model_structure(structure)

    @classmethod
    def register_model_styling(cls, styling: dict):
        """
        Register model styling with the process admin site.

        Parameters
        ----------
        styling : dict
            A dictionary representing the model styling to be registered.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite
        if styling: processAdminSite.register_model_styling(styling)

    @classmethod
    def register_widget_structure(cls, structure):
        """
        Register a widget structure with the process admin site.

        Parameters
        ----------
        structure : dict
            A dictionary representing the widget structure to be registered.
        """
        from lex.lex_app.ProcessAdminSettings import processAdminSite
        if structure: processAdminSite.register_widget_structure(structure)