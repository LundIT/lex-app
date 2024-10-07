def get_user_name(request):
    """
    Retrieve the user's name from the request.

    If the request headers contain "JIRA", a default name is returned.
    Otherwise, the name is extracted from the request's authentication information.

    Parameters
    ----------
    request : object
        The request object containing headers and authentication information.

    Returns
    -------
    str
        The user's name.
    """
    if "JIRA" in request.headers:
        return "Created by Jira"
    return f"{request.auth['name']} ({request.auth['sub']})"


def get_user_email(request):
    """
    Retrieve the user's email from the request.

    If the request headers contain "JIRA", a default email is returned.
    Otherwise, the email is extracted from the request's authentication information.

    Parameters
    ----------
    request : object
        The request object containing headers and authentication information.

    Returns
    -------
    str
        The user's email.
    """
    if "JIRA" in request.headers:
        return "jira@mail.com"
    return request.auth['email']
