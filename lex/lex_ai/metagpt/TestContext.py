import yaml
from pathlib import Path
class TestContext:
    def __init__(self):
        self._prompts = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load prompts from the YAML file."""
        prompts_path = Path(__file__).parent / 'test_context.yaml'
        try:
            with open(prompts_path, 'r', encoding='utf-8') as file:
                self._prompts = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompts file not found at {prompts_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing prompts YAML file: {str(e)}")

    def get_test_context(self, prompt_name: str) -> str:
        """
        Get a specific prompt by name.

        Args:
            prompt_name: The name of the prompt to retrieve

        Returns:
            The prompt text

        Raises:
            KeyError: If the prompt name doesn't exist
        """
        try:
            return self._prompts[prompt_name]
        except KeyError:
            raise KeyError(f"Prompt '{prompt_name}' not found in prompts.yaml")

    def list_prompts(self) -> list:
        """List all available prompt names."""
        return list(self._prompts.keys())

    def reload_prompts(self):
        """Reload prompts from the YAML file."""
        self._load_prompts()
