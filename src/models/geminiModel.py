"""
Gemini model implementation using the official google-genai library.
"""
import os

from google import genai

from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)

class GeminiModel():
    """
    Gemini API model implementation using google-genai.
    """

    def __init__(self):
        self._load_model()

    def _load_model(self) -> None:
        """Initializes the client."""
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.model = "gemma-3-4b-it"

    def generate(self, prompt: str, **kwargs) -> str:
        """Generates text for a single prompt."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        logger.info(f"Generated response: {response.text[:100]}...")
        return response.text

