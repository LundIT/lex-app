import os
from pathlib import Path
import re
from typing import Dict, Optional


class ProjectGenerator:
    def __init__(self, project_name: str, base_dir: Optional[str] = None):
        """
        Initialize project structure generator

        Args:
            project_name: Name of the project
            base_dir: Optional base directory (defaults to current working directory)
        """
        self.project_name =project_name
        self.base_dir = base_dir or os.getcwd()
        self.project_path = os.path.join(self.base_dir, project_name)

        # Create initial project structure
        self._create_base_structure()

    def _create_base_structure(self):
        """Creates the initial project structure with necessary directories"""
        base_dirs = [
            'Tests',
            'migrations',
        ]

        # Create base directories
        for dir_name in base_dirs:
            dir_path = os.path.join(self.project_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            init_path = os.path.join(dir_path, '__init__.py')
            Path(init_path).touch()

        # Create base config files
        self._create_config_files()

    def _create_config_files(self):
        """Creates basic configuration files"""
        config_files = {
            'config/settings.py': '''
# Project Settings
DEBUG = True
DATABASE = {
    'name': 'default',
    'engine': 'django.db.backends.sqlite3',
}
''',
            'config/__init__.py': '',
            '__init__.py': '',
            'README.md': f'# {self.project_name}\n\nAuto-generated project structure',
            '.gitignore': '''
__pycache__/
*.py[cod]
*$py.class
.env
.venv
env/
venv/
.idea/
.vscode/
*.egg-info/
dist/
build/
'''
        }

        for file_path, content in config_files.items():
            full_path = os.path.join(self.project_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())

    def parse_codes_with_filenames(self, markdown_content: str) -> dict:
        """Extract file paths and code content from markdown"""
        # Pattern to match Python code blocks
        code_pattern = r"```python(.*?)```"

        # Pattern to match file paths from headers
        file_path_pattern = r"###\s*(.*?\.py)"

        # Find all Python code blocks and file paths
        code_blocks = re.findall(code_pattern, markdown_content, re.DOTALL)
        file_paths = re.findall(file_path_pattern, markdown_content)

        # Pair file paths with code blocks
        parsed_files = {}
        for i, code in enumerate(code_blocks):
            if i < len(file_paths):
                file_path = file_paths[i].strip()
                parsed_files[file_path] = code.strip()
            else:
                print(f"Warning: Code block {i} has no corresponding file path")

        return parsed_files

    def add_file(self, file_path: str, content: str):
        """
        Add a new file to the project structure

        Args:
            file_path: Path to the file relative to src directory
            content: Content of the file
        """
        content = list(self.parse_codes_with_filenames(content).items())[0][1]
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/').strip('/')

        # Full path including project and src directory
        full_path = os.path.join(self.project_path, '', normalized_path)

        # Create all parent directories
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Create __init__.py files in all parent directories
        self._create_init_files(os.path.dirname(full_path))

        # Write the file content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Created file: {full_path}")

    def _create_init_files(self, directory: str):
        """
        Create __init__.py files in all parent directories

        Args:
            directory: Starting directory
        """
        current_dir = directory
        while current_dir.startswith(self.project_path):
            init_file = os.path.join(current_dir, '__init__.py')
            if not os.path.exists(init_file):
                Path(init_file).touch()
                print(f"Created __init__.py in: {current_dir}")
            current_dir = os.path.dirname(current_dir)

    def get_project_path(self) -> str:
        """Get the full path to the project"""
        return self.project_path