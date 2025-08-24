from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(content: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[str]:
    """
    Splits a large text content into smaller, manageable chunks.

    Args:
        content: The text content to be split.
        chunk_size: The maximum size of each chunk (in characters).
        chunk_overlap: The number of characters to overlap between chunks.

    Returns:
        A list of text chunks.
    """
    if not content:
        return []
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(content)