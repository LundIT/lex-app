import contextvars
from uuid import uuid4

# Define a context variable
context_id = contextvars.ContextVar('context_id', default={'context_id': '', 'request_obj': ''})

# Context manager to set operation id
class OperationContext:
    """
    Context manager to set and manage an operation ID for a request.

    This context manager sets a unique operation ID for each request if one
    does not already exist. The operation ID and request object are stored
    in a context variable.

    Parameters
    ----------
    request : Any
        The request object associated with the operation.
    """
    
    def __init__(self, request):
        """
        Initialize the OperationContext with a request object.

        Parameters
        ----------
        request : Any
            The request object associated with the operation.
        """
        self.request = request
    
    def __enter__(self):
        """
        Enter the runtime context related to this object.

        This method is called when the execution flow enters the context
        of the `with` statement. It sets a new operation ID if one doesn't
        already exist.

        Returns
        -------
        dict
            The context variable containing the operation ID and request object.
        """
        # Set a new operation id if one doesn't already exist
        if not context_id.get()['context_id']:
            context_id.set({'context_id': str(uuid4()),
                            'request_obj': self.request})
        return context_id.get()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        This method is called when the execution flow exits the context
        of the `with` statement. It can be used to reset or clear the
        operation ID if necessary.

        Parameters
        ----------
        exc_type : type
            The exception type, if an exception was raised.
        exc_val : Exception
            The exception instance, if an exception was raised.
        exc_tb : traceback
            The traceback object, if an exception was raised.
        """
        # Optionally, reset or clear the operation id here if necessary
        pass