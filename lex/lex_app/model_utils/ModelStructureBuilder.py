import importlib
import os
from typing import Dict

from lex_app.model_utils.parse_utils import ModelStructure


class ModelStructureBuilder:
    """
    A builder class for constructing model structures from various sources.

    Attributes
    ----------
    repo : str
        The repository name.
    model_structure : dict
        The structure of the model.
    model_styling : dict
        The styling information of the model.
    widget_structure : list
        The structure of the widgets.
    """
    def __init__(self, repo: str = ""):
        """
        Initialize the ModelStructureBuilder.

        Parameters
        ----------
        repo : str, optional
            The repository name (default is an empty string).
        """
        self.repo = repo
        self.model_structure = {}
        self.model_styling = {}
        self.widget_structure = []

    def extract_from_yaml(self, path: str):
        """
        Extract model structure and styling from a YAML file.

        Parameters
        ----------
        path : str
            The path to the YAML file.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file format is not YAML.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        if not path.endswith('.yaml'):
            raise ValueError(f"Invalid file format: {path}")

        info = ModelStructure(path)
        self.model_structure = info.structure
        self.model_styling = info.styling


    def extract_and_save_structure(self, full_module_name: str) -> None:
        """
        Extract and save structure from a module.

        Parameters
        ----------
        full_module_name : str
            The full name of the module to import.

        Raises
        ------
        ImportError
            If the module cannot be imported.
        """
        try:
            module = importlib.import_module(full_module_name)
        except ImportError as e:
            raise ImportError(f"Failed to import module {full_module_name}: {e}")

        structure_methods = {
            "model_structure": "get_model_structure",
            "widget_structure": "get_widget_structure",
            "model_styling": "get_model_styling",
        }

        for attr, method_name in structure_methods.items():
            if hasattr(module, method_name):
                try:
                    setattr(self, attr, getattr(module, method_name)())
                except Exception as e:
                    print(f"Error calling {method_name}: {e}")
            else:
                print(f"Warning: {method_name} not found in {full_module_name}")

    def get_extracted_structures(self):
        """
        Get the extracted structures.

        Returns
        -------
        dict
            A dictionary containing the model structure, widget structure, and model styling.
        """
        return {
            "model_structure": self.model_structure,
            "widget_structure": self.widget_structure,
            "model_styling": self.model_styling,
        }

    def build_structure(self, models) -> Dict:
        """
        Build the model structure from the given models.

        Parameters
        ----------
        models : dict
            A dictionary of models.

        Returns
        -------
        dict
            The constructed model structure.
        """
        # TODO: Filter models by repo
        for model_name, model in models.items():
            if self.repo not in model.__module__:
                continue
            path = self._get_model_path(model.__module__)
            self._insert_model_to_structure(path, str(model_name).lower())

        self._add_reports_to_structure()
        return self.model_structure

    def _get_model_path(self, path) -> str:
        """
        Get the model path relative to the repository.

        Parameters
        ----------
        path : str
            The full module path.

        Returns
        -------
        str
            The relative model path.

        Raises
        ------
        ValueError
            If the repository is not found in the module path.
        """
        try:
            module_parts = path.split('.')
            repo_index = module_parts.index(self.repo)
            return '.'.join(module_parts[repo_index + 1:-1])
        except ValueError as e:
            print(f"Path: {path}")

    def _insert_model_to_structure(self, path: str, name: str):
        """
        Insert a model into the structure.

        Parameters
        ----------
        path : str
            The path where the model should be inserted.
        name : str
            The name of the model.
        """
        current = self.model_structure
        for p in path.split('.'):
            if p not in current:
                current[p] = {}
            current = current[p]
        current[name] = None


    def _add_reports_to_structure(self):
        """
        Add predefined reports to the model structure.
        """
        self.model_structure['Z_Reports'] = {'userchangelog': None, 'calculationlog': None, 'log': None}
        if os.getenv("IS_STREAMLIT_ENABLED") == "true":
            self.model_structure['Streamlit'] = {'streamlit': None}
