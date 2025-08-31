"""
Hugging Face model implementation using the official Hugging Face library.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)


class HuggingFaceModel:
    """Hugging Face model implementation using the official Hugging Face library."""

    def __init__(self):
        self.model = "Qwen/Qwen3-4B-Thinking-2507:nscale"
        self._load_model()

    def _load_model(self) -> None:
        """Initializes the Hugging Face model."""
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=os.environ.get("HF_TOKEN"),
        )

    def generate(self, prompt: str) -> str:
        """Generates text for a single prompt."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        response = response.choices[0].message.content.split("</think>")[1].strip().replace("\n\n", "")
        logger.info(f"Generated response: {response[:100]}...")
        return response

if __name__ == "__main__":
    model = HuggingFaceModel()
    print(model.generate("Hello, how are you?"))