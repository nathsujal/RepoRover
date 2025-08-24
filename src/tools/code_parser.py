import ast
import logging
from typing import Set, Tuple, Dict, List, Any

logger = logging.getLogger(__name__)

class CodeVisitor(ast.NodeVisitor):
    """
    Traverses an Abstract Syntax Tree to find functions, classes, and their
    detailed relationships, including calls, inheritance, imports, and decorators.
    Now also extracts the actual source code content of functions.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        # Store the original source code lines for extraction
        self._source_lines = None
        self._load_source_lines()
        
        # --- Entities ---
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.classes: Dict[str, Dict[str, Any]] = {}

        # --- Relationships ---
        self.calls: Set[Tuple[str, str]] = set()
        self.imports: Dict[str, str] = {}
        self.inheritance: Set[Tuple[str, str]] = set() # (child, parent)
        self.class_methods: Set[Tuple[str, str]] = set() # (class, method)

        # --- Context Tracking ---
        self._context_stack: List[str] = []

    def _load_source_lines(self):
        """Load the source file lines for content extraction."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._source_lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to load source lines from {self.file_path}: {e}")
            self._source_lines = []

    def _extract_source_content(self, node: ast.AST) -> str:
        """Extract the source code content for a given AST node."""
        if not self._source_lines or not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return ""
        
        try:
            # AST line numbers are 1-based, list indices are 0-based
            start_line = node.lineno - 1
            end_line = node.end_lineno
            
            # Extract the lines and join them
            content_lines = self._source_lines[start_line:end_line]
            return ''.join(content_lines).rstrip()
        except Exception as e:
            logger.error(f"Failed to extract content for node at line {getattr(node, 'lineno', 'unknown')}: {e}")
            return ""

    def _get_current_context_id(self, entity_name: str) -> str:
        """Generates a unique ID for an entity based on its context."""
        return ":".join(self._context_stack + [entity_name])

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Captures class definitions and inheritance."""
        class_name = node.name
        parent_classes = [base.id for base in node.bases if isinstance(base, ast.Name)]
        
        self.classes[class_name] = {
            "file_path": self.file_path,
            "parent_classes": parent_classes,
            "content": self._extract_source_content(node)
        }
        
        for parent in parent_classes:
            self.inheritance.add((class_name, parent))

        self._context_stack.append(class_name)
        self.generic_visit(node)
        self._context_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Captures function definitions, arguments, decorators, and source content."""
        function_name = node.name
        
        # Determine the context (class method or standalone function)
        parent_class = None
        if len(self._context_stack) > 0 and self._context_stack[-1] in self.classes:
            parent_class = self._context_stack[-1]
            self.class_methods.add((parent_class, function_name))

        self.functions[function_name] = {
            "file_path": self.file_path,
            "docstring": ast.get_docstring(node),
            "args": [arg.arg for arg in node.args.args],
            "decorators": [dec.id for dec in node.decorator_list if isinstance(dec, ast.Name)],
            "parent_class": parent_class,
            "content": self._extract_source_content(node)
        }
        
        self._context_stack.append(function_name)
        self.generic_visit(node)
        self._context_stack.pop()

    def visit_Call(self, node: ast.Call):
        """Captures function calls."""
        if not self._context_stack:
            self.generic_visit(node)
            return
            
        caller_name = self._context_stack[-1]

        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name:
            self.calls.add((caller_name, callee_name))

        self.generic_visit(node)


def parse_python_file(file_path: str) -> CodeVisitor:
    """
    Reads and parses a Python file, returning a visitor object with the extracted data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)
        visitor = CodeVisitor(file_path=file_path)
        visitor.visit(tree)
        return visitor
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return CodeVisitor(file_path=file_path)

# --- Test Block ---
if __name__ == "__main__":
    import os

    sample_code = """
import logging
from functools import wraps

def my_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print("Calling decorated function")
        return f(*args, **kwargs)
    return wrapper

class Vehicle:
    def start_engine(self):
        logging.info("Engine started.")

class Car(Vehicle):
    def __init__(self, make):
        self.make = make

    @my_decorator
    def drive(self, speed):
        self.start_engine()
        print(f"Driving at {speed} mph.")

def main():
    my_car = Car("Toyota")
    my_car.drive("fast")
"""
    test_file_name = "_test_code_parser.py"
    with open(test_file_name, "w") as f:
        f.write(sample_code)

    print(f"--- Parsing {test_file_name} ---")
    visitor = parse_python_file(test_file_name)

    if visitor:
        print("\n[+] Discovered Functions:")
        for name, details in visitor.functions.items():
            print(f"  - {name}({', '.join(details['args'])})")
            if details['decorators']:
                print(f"    Decorators: {', '.join(details['decorators'])}")
            print(f"    Content:\n{details['content']}")
            print("    " + "-" * 50)

        print("\n[+] Discovered Classes & Inheritance:")
        for name, details in visitor.classes.items():
            parents = details.get('parent_classes', [])
            print(f"  - {name}" + (f" (inherits from {', '.join(parents)})" if parents else ""))
            print(f"    Content:\n{details['content']}")
            print("    " + "-" * 50)

        print("\n[+] Discovered Class Methods (Class -> Method):")
        for cls, method in visitor.class_methods:
            print(f"  - {cls} -> {method}")
            
        print("\n[+] Discovered Calls (Caller -> Callee):")
        for caller, callee in visitor.calls:
            print(f"  - {caller} -> {callee}")

    os.remove(test_file_name)
    print(f"\n--- Cleaned up {test_file_name} ---")