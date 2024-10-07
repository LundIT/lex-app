from functools import wraps


def LexSingleton(cls):
    """
    A decorator to make a class a singleton (only one instance).

    This decorator ensures that only one instance of the class exists.
    If an instance already exists, it returns the existing instance.

    Parameters
    ----------
    cls : type
        The class to be turned into a singleton.

    Returns
    -------
    function
        A function that returns the singleton instance of the class.
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

