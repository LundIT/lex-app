import ast
import os

import networkx as nx
from metagpt.roles.role import Role

from lex.lex_ai.rag.rag import RAG


class LexRole(Role):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def extract_project_imports(self, code_string, project_name):
        result = []
        tree = ast.parse(code_string)

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module_path = node.module
                if module_path and module_path.startswith(project_name):
                    # Split the module path and get the last component (class name)
                    imported_class = node.names[0].name
                    result.append(imported_class)

        return result

    def get_dependencies(self, generated_code_dict):
        return {k: v for k, (_, _, v) in generated_code_dict.items()}

    def get_dependencies_redirected(self, generated_code_dict):
        dependencies = {k: v for k, (_, _, v) in generated_code_dict.items()}
        new_dependencies = {}

        for class_name, deps in dependencies.items():
            updated_deps = []
            for dep in deps:
                # Check if Upload version of dependency exists
                upload_dep = f"{dep}Upload"
                if upload_dep in generated_code_dict:
                    updated_deps.append(upload_dep)
                else:
                    updated_deps.append(dep)

            # Store the updated dependencies
            new_dependencies[class_name] = updated_deps

            # If this class has an Upload version, copy the dependencies to it
            upload_class = f"{class_name}Upload"
            if upload_class in generated_code_dict:
                new_dependencies[upload_class] = updated_deps
        new_dependencies = {k: v for k, v in new_dependencies.items() if f"{k}Upload" not in generated_code_dict}
        return new_dependencies
    def get_models_to_test(self, dependencies):
        G = nx.DiGraph(dependencies)

        sccs = list(nx.strongly_connected_components(G))
        return sccs

    def extract_relevant_code(self, class_set, generated_code_dict, dependencies):
        if isinstance(class_set, str):
            class_set = {class_set}

        all_dependent_classes = {d for cls in class_set for d in dependencies[cls]}


        return "\n".join([f"{generated_code_dict[cls][1]}" for cls in all_dependent_classes])

    def extract_relevant_json(self, class_set, generated_json_dict, dependencies):
        if isinstance(class_set, str):
            class_set = {class_set}

        all_dependent_classes = {d for cls in class_set for d in dependencies[cls]}


        return "\n".join([generated_json_dict[cls] for cls in all_dependent_classes if cls in generated_json_dict])
    def get_code_from_set(self, class_set, generated_code_dict):
        if isinstance(class_set, str):
            class_set = {class_set}

        return "\n\n".join([generated_code_dict[cls][1] for cls in class_set])


    def get_import_pool(self, project_name, all_classes):
        # Generate import pool
        import_pool = "\n".join([
            f"Inner ImporPath: from {project_name}.{path.replace(os.sep, '.').rstrip('.py')} import {class_name}"
            for class_name, path in all_classes
        ])
        import_pool += "\nLex App Import: from lex.lex_app.rest_api.fields.XLSX_field"
        import_pool += "\nLex App Import: from lex.lex_app.LexLogger.LexLogLevel"
        import_pool += "\nLex App Import: from lex.lex_app.LexLogger.LexLogger import LexLogger"
        import_pool += "\nLex App Import: from lex.lex_app.lex_models.LexModel import LexModel"
        import_pool += "\nLex App Import: from lex.lex_app.lex_models.CalculationModel import CalculationModel"

        import_pool += "\nExternal ImportPath: from django.db import models"
        import_pool += "\nExternal ImportPath: import pandas as pd"
        import_pool += "\nExternal ImportPath: import numpy as np"

        return import_pool


    def _combine_code(self, code_dict: dict) -> str:
        """Combines all code from the dictionary into a single string."""
        return "\n\n".join([
            f"### {t[0]}\n{t[1]}"
            for _, t in code_dict.items()
        ])
    def get_lex_app_context(self, prompt):
        rag = RAG()
        i, j = rag.memorize_dir(RAG.LEX_APP_DIR)

        # lex_app_context = "\n".join([rag.query_code("LexModel", i, j, top_k=1)[0],
        #                              rag.query_code("CalculationModel", i, j, top_k=1)[0],
        #                              rag.query_code("LexLogger", i, j, top_k=1)[0],
        #                              rag.query_code("XLSXField", i, j, top_k=1)[0]])
        lex_app_context = "\n".join(rag.query_code("LexModel, CalculationModel, XLSXField, LexLogger", i, j, top_k=30))


        return lex_app_context



    def extract_python_code_from_directory(self, directory_path):
        python_code_files = {}

        # Iterate over all files in the directory
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # Check if the file has a .py extension
                if (file.endswith(".py")
                        and not file.startswith("test_")
                        and not file.startswith("0")
                        and not file.startswith("_")):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract Python code using parse_code
                        extracted_code = content
                        # Add to dictionary with file name as key
                        python_code_files[file.split(".")[0]] = {"content": extracted_code, "path": file_path.split("./projects/")[-1]}

        return python_code_files
