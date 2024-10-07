from typing import Dict, Set, Optional

from django.db.models import Model

from lex.lex_app.lex_models.ModelModificationRestriction import ModelModificationRestriction
from lex.lex_app.rest_api.serializers import model2serializer
from .utils import title_for_model


class ModelContainer:
    """
    A container for a Django model class that provides various utilities and properties.

    Parameters
    ----------
    model_class : Model
        The Django model class to be contained.
    process_admin
        An admin process object that provides methods for processing the model.

    Attributes
    ----------
    model_class : Model
        The Django model class to be contained.
    process_admin
        An admin process object that provides methods for processing the model.
    dependent_model_containers : Set[ModelContainer]
        A set of dependent model containers.
    obj_serializer
        A serializer for the model class, if applicable.
    """
    def __init__(self, model_class: Model, process_admin) -> None:
        self.model_class = model_class
        self.process_admin = process_admin
        self.dependent_model_containers: Set['ModelContainer'] = set()
        self.obj_serializer = model2serializer(self.model_class, self.process_admin.get_fields_in_table_view(
            self.model_class)) if hasattr(model_class, '_meta') else None

    @property
    def id(self) -> str:
        """
        Get the identifier for the model.

        Returns
        -------
        str
            The model name if available, otherwise the class name in lowercase.
        """
        return self.model_class._meta.model_name if hasattr(self.model_class,
                                                            '_meta') else self.model_class.__name__.lower()

    @property
    def title(self) -> str:
        """
        Get the title for the model.

        Returns
        -------
        str
            The title for the model.
        """
        return title_for_model(self.model_class) if hasattr(self.model_class, '_meta') else self.model_class.__name__

    @property
    def pk_name(self) -> Optional[str]:
        """
        Get the primary key name for the model.

        Returns
        -------
        Optional[str]
            The primary key name if available, otherwise None.
        """
        return self.model_class._meta.pk.name if hasattr(self.model_class, '_meta') else None

    def get_modification_restriction(self) -> ModelModificationRestriction:
        """
        Get the modification restriction for the model.

        Returns
        -------
        ModelModificationRestriction
            The modification restriction for the model.
        """
        return getattr(self.model_class, 'modification_restriction', ModelModificationRestriction())

    def get_general_modification_restrictions_for_user(self, user) -> Dict[str, bool]:
        """
        Get the general modification restrictions for a user.

        Parameters
        ----------
        user
            The user for whom to get the modification restrictions.

        Returns
        -------
        Dict[str, bool]
            A dictionary with the general modification permissions for the user.
        """
        restriction = self.get_modification_restriction()
        return {
            'can_read_in_general': restriction.can_read_in_general(user, None),
            'can_modify_in_general': restriction.can_modify_in_general(user, None),
            'can_create_in_general': restriction.can_create_in_general(user, None),
            'can_delete_in_general': restriction.can_delete_in_general(user, None)
        }
