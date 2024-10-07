from lex.lex_app.lex_models.ModelModificationRestriction import ModelModificationRestriction


class AdminReportsModificationRestriction(ModelModificationRestriction):
    """
    Restriction class for admin reports modification.

    This class inherits from ModelModificationRestriction and defines
    specific permissions for reading, modifying, creating, and deleting
    admin reports.

    Methods
    -------
    can_read_in_general(user, violations)
        Checks if the user can read in general.
    can_modify_in_general(user, violations)
        Checks if the user can modify in general.
    can_create_in_general(user, violations)
        Checks if the user can create in general.
    can_delete_in_general(user, violations)
        Checks if the user can delete in general.
    can_be_read(instance, user, violations)
        Checks if the instance can be read by the user.
    can_be_modified(instance, user, violations)
        Checks if the instance can be modified by the user.
    can_be_created(instance, user, violations)
        Checks if the instance can be created by the user.
    can_be_deleted(instance, user, violations)
        Checks if the instance can be deleted by the user.
    """

    def can_read_in_general(self, user, violations):
        """
        Checks if the user can read in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can read in general, False otherwise.
        """
        return True

    def can_modify_in_general(self, user, violations):
        """
        Checks if the user can modify in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can modify in general, False otherwise.
        """
        return False

    def can_create_in_general(self, user, violations):
        """
        Checks if the user can create in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can create in general, False otherwise.
        """
        return False

    def can_delete_in_general(self, user, violations):
        """
        Checks if the user can delete in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can delete in general, False otherwise.
        """
        return False

    def can_be_read(self, instance, user, violations):
        """
        Checks if the instance can be read by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be read by the user, False otherwise.
        """
        return True

    def can_be_modified(self, instance, user, violations):
        """
        Checks if the instance can be modified by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be modified by the user, False otherwise.
        """
        return False

    def can_be_created(self, instance, user, violations):
        """
        Checks if the instance can be created by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be created by the user, False otherwise.
        """
        return False

    def can_be_deleted(self, instance, user, violations):
        """
        Checks if the instance can be deleted by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be deleted by the user, False otherwise.
        """
        return False


class ExampleModelModificationRestriction(ModelModificationRestriction):
    """
    Example restriction class for model modification.

    This class inherits from ModelModificationRestriction and defines
    example permissions for reading, modifying, and creating models.

    Methods
    -------
    can_read_in_general(user, violations)
        Checks if the user can read in general.
    can_modify_in_general(user, violations)
        Checks if the user can modify in general.
    can_create_in_general(user, violations)
        Checks if the user can create in general.
    can_be_read(instance, user, violations)
        Checks if the instance can be read by the user.
    can_be_modified(instance, user, violations)
        Checks if the instance can be modified by the user.
    can_be_created(instance, user, violations)
        Checks if the instance can be created by the user.
    """

    def can_read_in_general(self, user, violations):
        """
        Checks if the user can read in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can read in general, False otherwise.
        """
        pass

    def can_modify_in_general(self, user, violations):
        """
        Checks if the user can modify in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can modify in general, False otherwise.
        """
        pass

    def can_create_in_general(self, user, violations):
        """
        Checks if the user can create in general.

        Parameters
        ----------
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the user can create in general, False otherwise.
        """
        pass

    def can_be_read(self, instance, user, violations):
        """
        Checks if the instance can be read by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be read by the user, False otherwise.
        """
        pass

    def can_be_modified(self, instance, user, violations):
        """
        Checks if the instance can be modified by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be modified by the user, False otherwise.
        """
        pass

    def can_be_created(self, instance, user, violations):
        """
        Checks if the instance can be created by the user.

        Parameters
        ----------
        instance : Model
            The instance being checked.
        user : User
            The user attempting the action.
        violations : list
            List of violations.

        Returns
        -------
        bool
            True if the instance can be created by the user, False otherwise.
        """
        pass
