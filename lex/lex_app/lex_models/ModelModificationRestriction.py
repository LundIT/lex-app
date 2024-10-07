from abc import ABC


class ModelModificationRestriction(ABC):
    """
    In order to restrict updating, deleting or creating instances of a certain model M, a class (say, X) inheriting
    this class @ModelModificationRestriction has to be defined and the desired methods have to be overwritten
    (further down in these docs it is explained which methods should be overwritten depending on your needs).
    Then, an instance of class X has to be added to the desired model A as class attribute 'modification_restriction'.

    The modification restriction works as follows:
    When a user tries to update or delete an instance of the model M, it is first checked whether the user is allowed
    to do this in general by calling the method @can_modify_in_general (default: True). If this results to False,
    an error is raised. Otherwise it is checked by calling the method @can_be_modified, if the user is allowed to
    modify the certain instance specifically. Again, if this results to False, an error is raised, otherwise
    the change is performed. The mechanism works similarly for creating an instance or reading instances.
    The parameter violations of the four methods is an array, where you can add error messages that explain
    why the user cannot perform the database change. These error messages are then shown in the raised error.
    """

    def can_create_in_general(self, user, violations):
        """
        Determines whether the given user is allowed to create instances of the model in general.

        Parameters
        ----------
        user : object
            The user attempting to create an instance.
        violations : list
            A list to which error messages can be added if the user is not allowed to create instances.

        Returns
        -------
        bool
            True if the user is allowed to create instances, False otherwise.
        """
        return True

    def can_read_in_general(self, user, violations):
        """
        Determines whether the given user is allowed to read instances of the model in general. If this results in
        false for a certain user, the user will not see the existence of this model at all.

        Parameters
        ----------
        user : object
            The user attempting to read instances.
        violations : list
            A list to which error messages can be added if the user is not allowed to read instances.

        Returns
        -------
        bool
            True if the user is allowed to read instances, False otherwise.
        """
        return True

    def can_modify_in_general(self, user, violations):
        """
        Determines whether the given user is allowed to update or delete instances of the model in general.

        Parameters
        ----------
        user : object
            The user attempting to modify instances.
        violations : list
            A list to which error messages can be added if the user is not allowed to modify instances.

        Returns
        -------
        bool
            True if the user is allowed to modify instances, False otherwise.
        """
        return True
    def can_delete_in_general(self, user, violations):
        """
        Determines whether the given user can delete instances of the model in general.

        Parameters
        ----------
        user : object
            The user attempting to delete instances.
        violations : list
            A list to which error messages can be added if the user is not allowed to delete instances.

        Returns
        -------
        bool
            True if the user is allowed to delete instances, False otherwise.
        """
        return True
    def can_be_read(self, instance, user, violations):
        """
        Determines whether the given user can read the given instance.

        Parameters
        ----------
        instance : object
            The instance the user is attempting to read.
        user : object
            The user attempting to read the instance.
        violations : list
            A list to which error messages can be added if the user is not allowed to read the instance.

        Returns
        -------
        bool
            True if the user is allowed to read the instance, False otherwise.
        """
        return True

    def can_be_modified(self, instance, user, violations, request_data):
        """
        Determines whether the given user can modify the given instance.
        Important: this method is called on the 'old' instance (i.e. before the modification)!

        Parameters
        ----------
        instance : object
            The instance the user is attempting to modify.
        user : object
            The user attempting to modify the instance.
        violations : list
            A list to which error messages can be added if the user is not allowed to modify the instance.
        request_data : dict
            The data that the user is attempting to use for the modification.

        Returns
        -------
        bool
            True if the user is allowed to modify the instance, False otherwise.
        """
        return True

    def can_be_deleted(self, instance, user, violations):
        """
        Determines whether the given user can delete the given instance.
        Important: this method is called on the 'old' instance (i.e. before the modification)!

        Parameters
        ----------
        instance : object
            The instance the user is attempting to delete.
        user : object
            The user attempting to delete the instance.
        violations : list
            A list to which error messages can be added if the user is not allowed to delete the instance.

        Returns
        -------
        bool
            True if the user is allowed to delete the instance, False otherwise.
        """
        return True

