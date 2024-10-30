import os
import faiss
import numpy as np
import pandas as pd
from langchain_openai import AzureOpenAIEmbeddings
import ast

class MethodInfo:
    def __init__(self, name, docstring, source_code, class_name, import_path):
        self.name = name
        self.docstring = docstring
        self.source_code = source_code
        self.class_name = class_name
        self.import_path = import_path

    def __str__(self):
        return f"Method: {self.name}\nClass: {self.class_name}\nImport Path: {self.import_path}\nDocstring: {self.docstring}\nSource Code:\n{self.source_code}"

class ClassInfo:
    def __init__(self, name, docstring, methods, source_code, import_path, imports):
        self.name = name
        self.docstring = docstring
        self.methods = methods
        self.source_code = source_code
        self.import_path = import_path
        self.imports = imports

    def __str__(self):
        return f"Class: {self.name}\nImport Path: {self.import_path}\n{'Docstring: ' + self.docstring if self.docstring else ''}\nSource Code:\n{self.source_code}"

class FunctionInfo:
    def __init__(self, name, docstring, source_code):
        self.name = name
        self.docstring = docstring
        self.source_code = source_code

    def __str__(self):
        return f"Function: {self.name}\nDocstring: {self.docstring}\nSource Code:\n{self.source_code}"
class RAG:
    LEX_APP_DIR = os.getenv("METAGPT_PROJECT_ROOT")
    def __init__(self):
        self.tables = []
        self.index = ""

    def memorize_dir(self, dir: str):
        self.index = f"{dir}/lex_app_index.index"
        return self.get_faiss_index(dir, self.index)

    def parse_source_code(self, file_content, file_path):
        """Parses the source code to extract top-level classes, functions, comments, and source code."""
        tree = ast.parse(file_content)
        structure = {}

        # Extract the module name by converting the file path to a Python import path
        relative_path = os.path.relpath(file_path, start=self.LEX_APP_DIR)
        module_name = relative_path.replace(os.sep, ".").rstrip(".py")

        visitor = TopLevelVisitor(file_content, module_name)
        visitor.visit(tree)

        if visitor.classes:
            structure["classes"] = visitor.classes
        if visitor.functions:
            structure["functions"] = visitor.functions
        return structure

    def read_xlsx_columns(self, file_path: str) -> dict:
        """
        Reads an XLSX file and extracts the table names and their columns.

        :param file_path: Path to the XLSX file
        :return: Dictionary with table names as keys and list of columns as values
        """
        xlsx_data = pd.read_excel(file_path, sheet_name=None)
        table_columns = {table: df.columns.tolist() for table, df in xlsx_data.items()}
        return table_columns

    def load_and_parse_directory(self, directory):
        """Loads and parses all Python files in the given directory."""
        project_structure = {}

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        structure = self.parse_source_code(content, file_path)
                        if structure:
                            project_structure[file] = structure
                if file.endswith('.xlsx'):
                    file_path = os.path.join(root, file)
                    table_columns = pd.read_excel(file_path)
                    self.tables.append(table_columns.head().__str__())


        return project_structure

    # Set up Azure OpenAI embeddings
    embeddings = AzureOpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_version="2023-05-15",
        azure_endpoint="https://lund-openai-instance-eastus.openai.azure.com",
        api_key="0c211119a6624d38a367bc9f79e148b2"
    )

    def get_embeddings(self, text):
        return self.embeddings.embed_query(text)

    def create_and_save_faiss_index(self, project_structure, index_path):
        embeddings_list = []
        index_to_chunk = {}
        i = 0

        for file, structure in project_structure.items():
            for class_info in structure.get("classes", []):
                chunk = str(class_info)
                embedding = self.get_embeddings(chunk)
                embeddings_list.append(embedding)
                index_to_chunk[i] = chunk
                i += 1

            for function_info in structure.get("functions", []):
                chunk = str(function_info)
                embedding = self.get_embeddings(chunk)
                embeddings_list.append(embedding)
                index_to_chunk[i] = chunk
                i += 1

        embeddings_array = np.array(embeddings_list)
        dimension = embeddings_array.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_array)
        faiss.write_index(index, index_path)
        return index, index_to_chunk

    def load_faiss_index(self, index_path):
        if not os.path.exists(index_path):
            return None
        return faiss.read_index(index_path)

    def get_faiss_index(self, source_directory, index_path):
        index = self.load_faiss_index(index_path)
        if index is None:
            project_structure = self.load_and_parse_directory(source_directory)
            index, index_to_chunk = self.create_and_save_faiss_index(project_structure, index_path)
        else:
            project_structure = self.load_and_parse_directory(source_directory)
            index_to_chunk = {}
            i = 0
            for file, structure in project_structure.items():
                for class_info in structure.get("classes", []):
                    chunk = str(class_info)
                    index_to_chunk[i] = chunk
                    i += 1
                for function_info in structure.get("functions", []):
                    chunk = str(function_info)
                    index_to_chunk[i] = chunk
                    i += 1
        return index, index_to_chunk

    def query_code(self, query, index, index_to_chunk, top_k=10, threshold=1.):
        query_embedding = np.array(self.get_embeddings(query)).reshape(1, -1)
        distances, indices = index.search(query_embedding, len(index_to_chunk))

        likelihoods = 1 / (1 + distances[0])
        total_likelihood = np.sum(likelihoods)
        cumulative_likelihood = 0
        selected_chunks = []

        for i, likelihood in enumerate(likelihoods):
            cumulative_likelihood += likelihood
            selected_chunks.append(index_to_chunk[indices[0][i]])
            if cumulative_likelihood / total_likelihood >= threshold or len(selected_chunks) >= top_k:
                break

        return selected_chunks + self.tables

class TopLevelVisitor(ast.NodeVisitor):
    def __init__(self, source_code, module_name):
        self.source_code = source_code
        self.module_name = module_name
        self.classes = []
        self.functions = []
        self.imports = []
        self.nesting_level = 0

    def visit_Import(self, node):
        self.imports.append(ast.get_source_segment(self.source_code, node))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports.append(ast.get_source_segment(self.source_code, node))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if self.nesting_level == 0:
            methods = []
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    method_info = MethodInfo(
                        name=body_item.name,
                        docstring=ast.get_docstring(body_item),
                        source_code=ast.get_source_segment(self.source_code, body_item),
                        class_name=node.name,
                        import_path=f"{self.module_name}.{node.name}"
                    )
                    methods.append(method_info)

            class_info = ClassInfo(
                name=node.name,
                docstring=ast.get_docstring(node),
                methods=methods,
                source_code=ast.get_source_segment(self.source_code, node),
                import_path=f"{self.module_name}.{node.name}",
                imports=self.imports
            )
            self.classes.append(class_info)
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_FunctionDef(self, node):
        if self.nesting_level == 0:
            function_info = FunctionInfo(
                name=node.name,
                docstring=ast.get_docstring(node),
                source_code=ast.get_source_segment(self.source_code, node)
            )
            self.functions.append(function_info)
        self.generic_visit(node)