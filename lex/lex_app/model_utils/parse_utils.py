import yaml

class ModelStructure:
    """
    A class to represent the structure and styling of a model.

    Attributes
    ----------
    path : str
        Path to the YAML file containing model information.
    structure : dict
        Dictionary to store the model structure.
    styling : dict
        Dictionary to store the model styling.
    """
    def __init__(self, path: str):
        """
        Initialize the ModelStructure with the path to the YAML file.

        Parameters
        ----------
        path : str
            The path to the YAML file containing model information.
        """
        self.path = path
        self.structure = {}
        self.styling = {}

        self._load_info()

    def _load_info(self):
        """
        Load model information from the YAML file.

        This method reads the YAML file specified by the path attribute
        and populates the structure and styling attributes with the
        corresponding data from the file.
        """
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        try:
            self.structure = data['model_structure']
        except (KeyError, TypeError):
            print("Error: Structure is not defined in the model info file")
        try:
            self.styling = data['model_styling']
        except (KeyError, TypeError):
            print("Error: Styling is not defined in the model info file")

    def structure_is_defined(self):
        """
        Check if the model structure is defined.

        Returns
        -------
        bool
            True if the model structure is defined, False otherwise.
        """
        return bool(self.structure)