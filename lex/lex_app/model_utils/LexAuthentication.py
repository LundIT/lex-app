from lex_app.decorators.LexSingleton import LexSingleton


@LexSingleton
class LexAuthentication:
    """
    A singleton class for handling authentication settings.

    This class uses the LexSingleton decorator to ensure that only one instance
    of the class exists. It dynamically loads attributes from a given settings
    module.

    Methods
    -------
    load_settings(auth_module)
        Dynamically loads attributes from the provided settings module.
    """
    def load_settings(self, auth_module):
        """
        Dynamically load attributes from the settings module.

        Parameters
        ----------
        auth_module : module
            The module from which to load authentication settings.
        """
        # Dynamically load attributes from the settings module
        for attr in dir(auth_module):
            if not attr.startswith("__"):  # Avoid loading built-in attributes
                print(f"Loading attribute: {attr}")
                setattr(self, attr, getattr(auth_module, attr))
