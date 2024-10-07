from functools import wraps


def LexSingleton(cls):
    """
    Decorator to make a class a singleton.

    Ensures that only one instance of the class is created. If an instance
    already exists, it returns the existing instance.

    Parameters
    ----------
    cls : type
        The class to be made a singleton.

    Returns
    -------
    function
        A wrapper function that returns the singleton instance of the class.
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

