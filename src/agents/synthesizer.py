"""
Synthesizer Agent: Generates a final, human-readable response from the collected data of a query plan.
"""

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

    def _create_synthesis_prompt(self, question: str, plan_results: List[Dict[str, Any]], conversation_history: str, persona: Dict[str, Any]) -> str:
        """Create a prompt for response synthesis."""
        context = ""
        for i, step in enumerate(plan_results):
            context += f"Step {i+1}: Tool `{step['tool']}` was called with input `{step['tool_input']}`.\n"
            context += f"Result: {step['tool_output']}\n\n"

        persona_prompt = "You are a helpful AI assistant."
        if persona:
            persona_prompt = f"Your Persona: {persona.description}. Your instructions are: {' '.join(persona.instructions)}"


        return (
            f"{persona_prompt}\n\n"
            f"Based on the following conversation history, answer the user's latest question.\n"
            f"--- CONVERSATION HISTORY ---\n{conversation_history}\n--------------------------\n\n"
            f"You have run a series of tools to gather information. Here is the data you collected:\n"
            f"--- TOOL RESULTS ---\n{context}\n---------------------\n\n"
            f"User's final question: {question}\n\n"
            f"Provide a clear, concise, and helpful answer to the user's question, keeping your persona and the conversation history in mind."
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes a response from a query plan."""
        question = input_data.get("question")
        plan = input_data.get("plan")

        conversation_history = input_data.get("conversation_history", "No history available.")
        persona = input_data.get("persona")

        if not question or not plan:
            return {"status": "error", "message": "Question and plan are required."}

        logger.info(f"Synthesizing response for question: {question}")
        prompt = self._create_synthesis_prompt(question, plan, conversation_history, persona)
        
        try:
            response = self.model.generate(prompt)
            return {"status": "success", "response": response}
        except Exception as e:
            logger.exception("Error during response synthesis.")
            return {"status": "error", "message": str(e)}