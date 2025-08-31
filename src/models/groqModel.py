"""
Groq model implementation using the official LangChain integration.
"""
import os

from langchain_groq import ChatGroq

from dotenv import load_dotenv
from numpy.char import str_len
load_dotenv()

import logging
logger = logging.getLogger(__name__)

class GroqModel():
    """
    Groq API model implementation using langchain-groq.
    """

    def __init__(self):
        self.model = "llama-3.1-8b-instant"
        self._load_model()

    def _load_model(self) -> None:
        """Initializes the ChatGroq client from LangChain."""
        self.client = ChatGroq(
            model=self.model,
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def generate(self, prompt: str) -> str:
        """Generates text for a single prompt from the Groq API."""
        response = self.client.invoke(prompt).content
        logger.info(f"Generated response: {response[:100]}...")
        return response


if __name__ == "__main__":
    model = GroqModel()
    print(model.generate("Hello, how are you?"))