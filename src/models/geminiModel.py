"""
Groq model implementation using the official LangChain integration.
"""
import os

from google import genai

from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)

class GeminiModel():
    """
    Groq API model implementation using langchain-groq.
    """

    def __init__(self):
        self._load_model()

    def _load_model(self) -> None:
        """Initializes the ChatGroq client from LangChain."""
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.model = "gemma-3-4b-it"

    def generate(self, prompt: str, **kwargs) -> str:
        """Generates text for a single prompt from the Groq API."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        logger.info(f"Generated response: {response.text[:50]}...")
        return response.text

