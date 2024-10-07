import copy

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from lex.lex_app.rest_api.model_collection.model_collection import ModelCollection


class ModelStructureObtainView(APIView):
    """
    View to obtain the model structure with user-specific restrictions.

    Attributes
    ----------
    http_method_names : list
        Allowed HTTP methods for this view.
    model_collection : ModelCollection, optional
        Collection of models.
    permission_classes : list
        Permissions required to access this view.
    get_model_structure_func : callable, optional
        Function to get the model structure.
    get_container_func : callable, optional
        Function to get the container for a model.
    """
    http_method_names = ['get']
    model_collection = None
    permission_classes = [HasAPIKey | IsAuthenticated]
    get_model_structure_func = None
    get_container_func = None


    def delete_restricted_nodes_from_model_structure(self, model_structure, user):
        """
        Delete nodes from the model structure that the user is restricted from accessing.

        Parameters
        ----------
        model_structure : dict
            The model structure.
        user : User
            The user object.
        """
        nodes = list(model_structure.keys())
        for n in nodes:
            if 'children' not in model_structure[n]:
                container = self.get_container_func(n)
                if not container.get_general_modification_restrictions_for_user(user)['can_read_in_general']:
                    del model_structure[n]

        for subTree in model_structure.values():
            if 'children' in subTree:
                self.delete_restricted_nodes_from_model_structure(subTree['children'], user)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to obtain the user-specific model structure.

        Parameters
        ----------
        request : Request
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            The response containing the user-specific model structure.
        """
        user = request.user
        # user_dependet_model_structure = copy.deepcopy(self.model_collection.model_structure_with_readable_names)
        user_dependet_model_structure = copy.deepcopy(self.get_model_structure_func())
        self.delete_restricted_nodes_from_model_structure(user_dependet_model_structure, user)
        return Response(user_dependet_model_structure)


class ModelStylingObtainView(APIView):
    """
    View to obtain the model styling with user-specific restrictions.

    Attributes
    ----------
    http_method_names : list
        Allowed HTTP methods for this view.
    model_collection : ModelCollection, optional
        Collection of models.
    permission_classes : list
        Permissions required to access this view.
    """
    http_method_names = ['get']
    model_collection: ModelCollection = None
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to obtain the user-specific model styling.

        Parameters
        ----------
        request : Request
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            The response containing the user-specific model styling.
        """
        user = request.user
        user_dependent_model_styling = self.model_collection.model_styling.copy()
        for key in user_dependent_model_styling.keys():
            # FIXME remove try-catch
            try:
                container = self.model_collection.get_container(key).model_class

                if hasattr(container, 'modification_restriction'):  # FIXME change these ugly calls of hasattr
                    # FIXME: this is only set if there is an entry in @user_dependent_model_styling for the model
                    #   if this is not the case (which mostly holds), then the restrictions are not transfered to the
                    #   frontend --> fix this via own route for modification_restriction (which is better anyway)
                    user_dependent_model_styling[key][
                        'can_read_in_general'] = container.modification_restriction.can_read_in_general(user,
                                                                                                        violations=None)
                    user_dependent_model_styling[key][
                        'can_modify_in_general'] = container.modification_restriction.can_modify_in_general(user,
                                                                                                            violations=None)
                    user_dependent_model_styling[key][
                        'can_create_in_general'] = container.modification_restriction.can_create_in_general(user,
                                                                                                            violations=None)
            except KeyError:
                # happens if key not in container
                pass

        return Response(user_dependent_model_styling)


class Overview(APIView):
    """
    View to obtain an HTML report overview.

    Attributes
    ----------
    http_method_names : list
        Allowed HTTP methods for this view.
    HTML_reports : dict, optional
        Dictionary of HTML report classes.
    """
    http_method_names = ['get']
    HTML_reports = None

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to obtain an HTML report.

        Parameters
        ----------
        request : Request
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            The response containing the HTML report.
        """
        user = request.user
        class_name = kwargs['report_name']
        html_report_class = self.HTML_reports[class_name]
        html = html_report_class().get_html(user)
        return Response(html)

class ProcessStructure(APIView):
    """
    View to obtain the structure of a process.

    Attributes
    ----------
    http_method_names : list
        Allowed HTTP methods for this view.
    processes : dict, optional
        Dictionary of process classes.
    """
    http_method_names = ['get']
    processes = None

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to obtain the structure of a process.

        Parameters
        ----------
        request : Request
            The request object.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        Response
            The response containing the process structure.
        """
        class_name = kwargs['process_name']
        process_class = self.processes[class_name]
        process_structure = process_class().get_structure()
        return Response(process_structure)
