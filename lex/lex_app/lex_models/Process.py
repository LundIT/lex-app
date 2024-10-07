from django.db.models import Model


class Process(Model):
    """
    Abstract base class for processes.

    This class serves as a template for creating process models.
    It is an abstract class and should not be instantiated directly.

    Methods
    -------
    get_structure()
        Abstract method that should be implemented by subclasses to define the structure of the process.
    """

    class Meta():
        """
        Meta options for the Process model.

        Attributes
        ----------
        abstract : bool
            Indicates that this is an abstract model.
        """
        abstract = True

    def get_structure(self):
        """
        Abstract method to get the structure of the process.

        This method must be implemented by subclasses.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")

