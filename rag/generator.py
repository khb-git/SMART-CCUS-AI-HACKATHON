"""
LLM generator using local Ollama (Llama 3.1).
"""

import logging
import ollama

logger = logging.getLogger(__name__)


class Generator:
    """Generates completions from a local Ollama LLM."""

    def __init__(self, model_name="llama3", temperature=0.2, max_tokens=128):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt):
        """Generate a completion using Ollama."""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert EPA Class VI carbon storage permit reviewer."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                }
            )

            return response["message"]["content"].strip()

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return "Error generating response with local LLM."