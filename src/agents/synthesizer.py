# src/agents/synthesizer.py
import logging
from typing import Any, Dict, List

from src.models.geminiModel import GeminiModel

logger = logging.getLogger(__name__)

class SynthesizerAgent:
    """
    The Synthesizer agent generates a final, human-readable response from the
    collected data of a query plan.
    """

    def __init__(self):
        self.name = "synthesizer"
        self.description = "Generates a final response from a query plan."
        self.model = GeminiModel()
        logger.info(f"{self.name} agent initialized.")

    def _create_synthesis_prompt(self, question: str, plan_results: List[Dict[str, Any]]) -> str:
        """Create a prompt for response synthesis."""
        context = ""
        for i, step in enumerate(plan_results):
            context += f"Step {i+1}: Tool `{step['tool']}` was called with input `{step['tool_input']}`.\n"
            context += f"Result: {step['tool_output']}\n\n"

        return (
            f"You are an expert code analyst. Your task is to answer the user's question based on the provided context from a series of tool calls.\n\n"
            f"The user's question is: {question}\n\n"
            f"Here is the context from the tool calls:\n"
            f"{context}"
            f"Please provide a clear and concise answer to the user's question based on this context. If the context is not sufficient, please state that."
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes a response from a query plan."""
        question = input_data.get("question")
        plan = input_data.get("plan")

        if not question or not plan:
            return {"status": "error", "message": "Question and plan are required."}

        logger.info(f"Synthesizing response for question: {question}")
        prompt = self._create_synthesis_prompt(question, plan)
        
        try:
            response = self.model.generate(prompt)
            return {"status": "success", "response": response}
        except Exception as e:
            logger.exception("Error during response synthesis.")
            return {"status": "error", "message": str(e)}