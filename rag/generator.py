"""
LLM generator — placeholder.

Final choice between Llama 3 and Mistral comes from LLM benchmarking
in the next phase. Until then, this module just defines the interface.
"""

import logging

logger = logging.getLogger(__name__)


class Generator:
    """Generates completions from a local LLM."""

    def __init__(self, model_path=None, temperature=0.2, max_tokens=512):
        self.model_path = model_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm = None

    def generate(self, prompt):
        """Generate a completion for the given prompt."""
        if self._llm is None:
            # TODO: from llama_cpp import Llama
            #       self._llm = Llama(model_path=str(self.model_path),
            #                         n_ctx=4096, verbose=False)
            logger.warning("Generator.generate not yet implemented")
            return "[generator not yet implemented]"
        # TODO: out = self._llm(prompt, max_tokens=self.max_tokens,
        #                       temperature=self.temperature, stop=["</s>"])
        #       return out["choices"][0]["text"].strip()
        return ""
