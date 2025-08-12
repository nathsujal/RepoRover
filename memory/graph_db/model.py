from pydantic import BaseModel
from typing import List

class ParsedFunction(BaseModel):
    """Represents a parsed function"""
    name: str
    line_start: int
    parameters: List[str]
    metadata: dict

class ParsedClass(BaseModel):
    """Represents a parsed class"""
    name: str
    line_start: int
    metadata: dict

class ParsedFile(BaseModel):
    """Represents a parsed file"""
    path: str
    functions: List[ParsedFunction]
    classes: List[ParsedClass]