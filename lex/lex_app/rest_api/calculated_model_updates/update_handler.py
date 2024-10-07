from lex.lex_app.lex_models.calculated_model import CalculatedModelMixin
from lex.lex_app.lex_models.process_admin_model import DependencyAnalysisMixin


def calc_and_save(entry):
    """
    Calculate and save the given entry.

    Parameters
    ----------
    entry : object
        The entry to be calculated and saved.
    """
    entry.calculate()
    entry.save()


class CalculatedModelUpdateHandler:
    """
    Handler for updating calculated models.

    This class manages the collection of models and the behavior to execute
    after saving a model.

    Attributes
    ----------
    instance : CalculatedModelUpdateHandler
        Singleton instance of the handler.
    model_collection : object
        Collection of models to be managed.
    post_save_behaviour : callable
        Function to be executed after saving a model.
    """
    instance = None

    def __init__(self):
        """
        Initialize the handler with default settings.
        """
        # TODO: Change file to rely on 'model_graph_store.py' instead
        self.model_collection = None
        self.post_save_behaviour = calc_and_save
        CalculatedModelUpdateHandler.instance = self

    def set_model_collection(self, model_collection):
        """
        Set the collection of models to be managed.

        Parameters
        ----------
        model_collection : object
            The collection of models.
        """
        self.model_collection = model_collection

    @staticmethod
    def set_post_save_behaviour(func):
        """
        Set the behavior to execute after saving a model.

        Parameters
        ----------
        func : callable
            The function to be executed.
        """
        CalculatedModelUpdateHandler.instance.post_save_behaviour = func

    @staticmethod
    def reset_post_save_behaviour():
        """
        Reset the post-save behavior to the default `calc_and_save`.
        """
        CalculatedModelUpdateHandler.instance.post_save_behaviour = calc_and_save

    @staticmethod
    def register_save(updated_entry):
        """
        Register a save operation for the updated entry and update dependent entries.

        Parameters
        ----------
        updated_entry : object
            The entry that has been updated.
        """
        # TODO: Properly handle this case
        if not issubclass(type(updated_entry), DependencyAnalysisMixin):
            return

        # Get all entries in calculated models dependent on 'updated_entry'
        dependent_entries = updated_entry.get_dependent_entries().keys()
        dependent_calculated_entries = list(
            filter(
                lambda entry: issubclass(type(entry), CalculatedModelMixin),
                dependent_entries
            )
        )

        # Update each such entry
        for entry in dependent_calculated_entries:
            CalculatedModelUpdateHandler.instance.post_save_behaviour(entry)
