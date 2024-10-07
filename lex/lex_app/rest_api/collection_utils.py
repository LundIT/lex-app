import functools


def flatten(lists):
    """
    Flattens a list of lists into a single list.

    Parameters
    ----------
    lists : list of lists
        The list of lists to be flattened.

    Returns
    -------
    list
        A single list containing all the elements of the input lists.
    """
    return functools.reduce(lambda list1, list2: list1 + list2, lists, [])
