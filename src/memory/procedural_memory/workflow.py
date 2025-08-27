"""
Defines the Pydantic models for procedural memory workflows.
"""
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Step(BaseModel):
    """A single step in a workflow."""
    name: str = Field(..., description="The name of the step.")
    agent: str = Field(..., description="The name of the agent to execute this step.")
    input: Optional[Dict[str, Any]] = Field(None, description="The input to pass to the agent's execute method.")
    output: Optional[str] = Field(None, description="The key to store the output under in the workflow context.")
    description: Optional[str] = Field(None, description="A description of what this step does.")

class Workflow(BaseModel):
    """A workflow composed of multiple steps."""
    name: str = Field(..., description="The name of the workflow.")
    description: Optional[str] = Field(None, description="A description of the workflow's purpose.")
    steps: List[Step] = Field(..., description="The sequence of steps in the workflow.")
    initial_context: Optional[Dict[str, Any]] = Field({}, description="Initial context for the workflow.")
