"""
Synthesizer Agent: Generates a final, human-readable response from the collected data of a query plan.
"""

import logging
from typing import Any, Dict, List

from src.models.groqModel import GroqModel

logger = logging.getLogger(__name__)

class SynthesizerAgent:
    """
    The Synthesizer agent generates a final, human-readable response from the
    collected data of a query plan.
    """

    def __init__(self):
        self.name = "synthesizer"
        self.description = "Generates a final response from a query plan."
        self.model = GroqModel()
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


        return f"""
{persona_prompt}

**Background Information:**
The following information was retrieved from the code repository to help you answer the user's question.
---
{context}
---

**Conversation History (for context on follow-up questions only, DO NOT mention it in your answer):**
---
{conversation_history}
---

**Your Task:**
Based *only* on the Background Information provided, answer the user's question in a direct, clear, and concise manner.

**CRITICAL RULES:**
1.  **Be Direct:** Do not talk about "tools," "data collection," "conversation history," or your own reasoning process. Just provide the answer as if you already knew it.
2.  **Synthesize, Don't Announce:** Seamlessly integrate the information into a natural, human-like response.
3.  **Handle Missing Information:** If the Background Information explicitly states that no information was found, your ONLY response must be to inform the user that you could not find the answer within the repository. Do not suggest further actions.

**User's Question:** {question}

**Answer:**
"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes a response from a query plan."""
        question = input_data.get("question")
        plan_results = input_data.get("plan")

        logger.info(f"Question: {question}")
        logger.info(f"Plan Results: {plan_results}")

        conversation_history = input_data.get("conversation_history", "No history available.")
        persona = input_data.get("persona")

        if not question or plan_results is None:
            return {"status": "error", "message": "Question and plan results are required."}

        logger.info(f"Synthesizing response for question: {question}")
        prompt = self._create_synthesis_prompt(question, plan_results, conversation_history, persona)
        
        try:
            response = self.model.generate(prompt)
            logger.info(f"Synthesized response: {response}")
            return {"status": "success", "response": response}
        except Exception as e:
            logger.exception("Error during response synthesis.")
            return {"status": "error", "message": str(e)}