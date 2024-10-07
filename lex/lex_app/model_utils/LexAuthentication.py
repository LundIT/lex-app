from lex_app.decorators.LexSingleton import LexSingleton


@LexSingleton
class LexAuthentication:
    """
    A singleton class for handling authentication settings.

    This class uses the LexSingleton decorator to ensure that only one instance
    of the class exists. It provides a method to dynamically load settings from
    a given authentication module.
    """
    def load_settings(self, auth_module):
        """
        Dynamically load attributes from the given settings module.

        This method iterates over the attributes of the provided module and
        sets them as attributes of the LexAuthentication instance, excluding
        built-in attributes.

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
