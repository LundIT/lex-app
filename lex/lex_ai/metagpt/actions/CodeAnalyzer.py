import ast
import os


class ProjectAnalyzer:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.issues = []

    def _validate_import_path(self, module_path: str) -> bool:
        """Validates if import path exists in project structure"""
        try:
            module_parts = module_path.split('.')
            current_path = ''

            for part in module_parts:
                current_path = os.path.join(current_path, part)
                if not os.path.exists(current_path) and not os.path.exists(current_path + '.py'):
                    return False
            return True
        except Exception:
            return False

    def _has_valid_fields(self, node: ast.ClassDef) -> bool:
        """Checks if model class has properly defined fields"""
        has_fields = False
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(child.value, ast.Call):
                            if isinstance(child.value.func, ast.Attribute):
                                if child.value.func.value.id == 'models':
                                    has_fields = True
                                    break
        return has_fields

    def _has_calculate_method(self, node: ast.ClassDef) -> bool:
        """Verifies if CalculationModel has calculate method"""
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                if child.name == 'calculate':
                    return True
        return False
    def analyze_project(self, directory_path: str):
        """Traverses project directory and analyzes all Python files"""
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
        return self.issues

    def analyze_file(self, file_path: str):
        """Analyzes a single Python file for issues"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            self._check_imports(tree, file_path)
            self._check_model_definitions(tree, file_path)
            self._check_calculation_methods(tree, file_path)
        except SyntaxError as e:
            self.issues.append({
                'file': file_path,
                'type': 'SyntaxError',
                'message': str(e)
            })

    def _check_imports(self, tree: ast.AST, file_path: str):
        """Validates import statements"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(self.project_name):
                    if not self._validate_import_path(node.module):
                        self.issues.append({
                            'file': file_path,
                            'type': 'ImportError',
                            'message': f"Invalid import path: {node.module}"
                        })

    def _check_model_definitions(self, tree: ast.AST, file_path: str):
        """Checks Django model definitions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if any(base in ['LexModel', 'CalculationModel'] for base in bases):
                    if not self._has_valid_fields(node):
                        self.issues.append({
                            'file': file_path,
                            'type': 'ModelError',
                            'message': f"Missing required fields in model {node.name}"
                        })

    def _check_calculation_methods(self, tree: ast.AST, file_path: str):
        """Validates calculation methods in CalculationModel classes"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                if 'CalculationModel' in bases:
                    if not self._has_calculate_method(node):
                        self.issues.append({
                            'file': file_path,
                            'type': 'MethodError',
                            'message': f"Missing calculate method in {node.name}"
                        })