#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """
    Set the default Django settings module and execute the command line utility.

    This function sets the 'DJANGO_SETTINGS_MODULE' environment variable to
    'lex_app.settings' and then attempts to import and execute Django's
    command-line utility. If Django is not installed or not available on the
    PYTHONPATH, it raises an ImportError with a descriptive message.

    Raises
    ------
    ImportError
        If Django is not installed or not available on the PYTHONPATH.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lex_app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
