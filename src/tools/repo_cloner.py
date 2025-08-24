import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

def clone_repo(repo_url: str, output_dir: str) -> str:
    """
    Clones a public GitHub repository to a specified directory.

    Args:
        repo_url: The URL of the GitHub repository.
        output_dir: The directory to clone the repository into.

    Returns:
        The local path to the cloned repository.
    """
    try:
        # Clear the directory if it exists to ensure a fresh clone
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        logger.info(f"Cloning repository from {repo_url} into {output_dir}...")
        Repo.clone_from(repo_url, output_dir)
        logger.info("Repository cloned successfully.")
        return output_dir
    except GitCommandError as e:
        logger.error(f"Failed to clone repository: {e}")
        raise ValueError(f"Could not clone repo from {repo_url}") from e

def scan_repository(repo_path: str) -> Dict[str, List[str]]:
    """
    Scans a repository and categorizes files by type.

    Args:
        repo_path: The local path to the cloned repository.

    Returns:
        A dictionary categorizing file paths (e.g., {'python': [...], 'markdown': [...]}).
    """
    categorized_files = {
        "python": [],
        "markdown": [],
        "other": []
    }
    
    ignore_dirs = ['.git', 'venv', 'env', '__pycache__']
    
    for root, dirs, files in os.walk(repo_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            file_path = str(Path(root) / file)
            if file.endswith('.py'):
                categorized_files['python'].append(file_path)
            elif file.endswith(('.md', '.mdx', '.txt')):
                categorized_files['markdown'].append(file_path)
            else:
                categorized_files['other'].append(file_path)
                
    return categorized_files