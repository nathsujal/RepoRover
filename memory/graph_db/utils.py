from typing import Optional, List, Dict
from pathlib import Path
import logging
from datetime import datetime
import ast
import re

from .model import ParsedFile, ParsedFunction, ParsedClass

logger = logging.getLogger(__name__)

def scan_repository(repo_path: str | Path) -> List[Dict]:
    """Scan repository and return file information"""
    files = []
    repo_path = Path(repo_path)
        
    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and not _should_ignore_file(file_path):
            try:
                stat = file_path.stat()
                language = _detect_language(file_path)
                lines_of_code = _count_lines_of_code(file_path)
                
                files.append({
                    "path": str(file_path),
                    "language": language,
                    "metadata": {
                        "size": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "lines_of_code": lines_of_code
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue
                    
    return files

def get_source_files(repo_path: str | Path) -> List[str]:
    """Get all source files in the repository"""
    source_extensions = {'.py', '.js', '.jsx', '.html', '.css', '.yaml', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rs'}
    files = []
        
    for file_path in Path(repo_path).rglob("*"):
        if (file_path.is_file() and 
            file_path.suffix.lower() in source_extensions and 
            not _should_ignore_file(file_path)):
            files.append(str(file_path))
                
    return files

def parse_file(file_path: str | Path) -> ParsedFile:
    """Parse a file and extract AST information"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # For Python files, use ast module
        if file_path.endswith('.py'):
            return _parse_python_file(content, file_path)
        else:
            # For other languages, implement basic regex-based parsing
            return _parse_generic_file(content, file_path)
                
    except Exception as e:
        logger.error(f"Failed to parse file {file_path}: {e}")
        return ParsedFile(path=file_path, functions=[], classes=[])
    
def _parse_python_file(content: str, file_path: str) -> ParsedFile:
    """Parse Python file using AST"""
    try:
        tree = ast.parse(content)
        functions = []
        classes = []
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(ParsedFunction(
                    name=node.name,
                    line_start=node.lineno,
                    parameters=[arg.arg for arg in node.args.args],
                    metadata={
                        "line_end": getattr(node, 'end_lineno', node.lineno),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "docstring": ast.get_docstring(node) or ""
                    }
                ))
                
            elif isinstance(node, ast.ClassDef):
                classes.append(ParsedClass(
                    name=node.name,
                    line_start=node.lineno,
                    metadata={
                        "line_end": getattr(node, 'end_lineno', node.lineno),
                        "docstring": ast.get_docstring(node) or "",
                        "bases": [base.id for base in node.bases if isinstance(base, ast.Name)]
                    }
                ))
            
        return ParsedFile(path=file_path, functions=functions, classes=classes)
            
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return ParsedFile(path=file_path, functions=[], classes=[])
    
def _parse_generic_file(content: str, file_path: str) -> ParsedFile:
    """Basic parsing for non-Python files using regex"""
    functions = []
    classes = []
        
    # Basic function detection (works for many C-style languages)
    function_pattern = r'^\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*\{'
    for i, line in enumerate(content.split('\n')):
        match = re.search(function_pattern, line)
        if match:
            functions.append(ParsedFunction(
                name=match.group(1),
                line_start=i + 1,
                parameters=[],
                metadata={}
            ))
        
    # Basic class detection
    class_pattern = r'^\s*(?:public|private)?\s*class\s+(\w+)'
    for i, line in enumerate(content.split('\n')):
        match = re.search(class_pattern, line)
        if match:
            classes.append(ParsedClass(
                name=match.group(1),
                line_start=i + 1,
                metadata={}
            ))
        
    return ParsedFile(path=file_path, functions=functions, classes=classes)

def _should_ignore_file(file_path: str | Path) -> bool:
    """Check if file should be ignored"""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    ignore_patterns = {
        '.git', '__pycache__', 'node_modules', '.pytest_cache',
        '.mypy_cache', 'venv', '.venv', 'env', '.env'
    }
        
    # Check if any part of the path contains ignore patterns
    for part in file_path.parts:
        if part in ignore_patterns or part.startswith('.'):
            return True
                
    # Check file extensions to ignore
    ignore_extensions = {
        '.pyc', '.pyo', '.log', '.tmp',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.class', '.jar'
        }
    if file_path.suffix in ignore_extensions:
        return True
            
    return False

def _detect_language(file_path: str | Path) -> str:
    """Detect the programming language of a file based on its extension"""
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.md': 'markdown',
        '.txt': 'text',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql'
    }
        
    return language_map.get(file_path.suffix.lower(), 'unknown')

def _count_lines_of_code(file_path: str | Path) -> int:
    """Count lines of code in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0
    
if __name__ == "__main__":
    repo_path = Path("/home/sujalnath/dev/projects/OrgGPT")
    # files_info = scan_repository(repo_path)
    # for file_info in files_info:
    #     print(f"File: {file_info['path']}, Language: {file_info['language']}, "
    #           f"Size: {file_info['metadata']['size']} bytes, "
    #           f"Last Modified: {file_info['metadata']['last_modified']}, "
    #           f"Lines of Code: {file_info['metadata']['lines_of_code']}")
    
    # source_files = get_source_files(repo_path)
    # print(f"\nSource files in {repo_path}:")
    # for file in source_files:
    #     print(file)

    print(parse_file("/home/sujalnath/dev/projects/OrgGPT/backend/app/services/embedding_service.py"))