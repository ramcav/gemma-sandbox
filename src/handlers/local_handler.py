import ollama
from typing import Any
from .llm_handler import LLMHandler

class LocalHandler(LLMHandler):
    """
    Handles chat logic for local models using Ollama.
    Inherits shared functionality from LLMHandler.
    """
    
    def __init__(self, model_name: str = "gemma3n:latest"):
        super().__init__(model_name)

    def _call_model(self, system_prompt: str) -> str:
        """Call Ollama with the prepared messages"""
        messages = self._prepare_messages_for_model(system_prompt)
        
        print("🤔 Thinking...")
        response = ollama.chat(
            model=self.model_name,
            messages=messages,
            format="json"  # Request structured JSON response
        )
        
        return response['message']['content']

    def _prepare_messages_for_model(self, system_prompt: str) -> Any:
        """Format messages for Ollama's expected format"""
        return [
            {"role": "system", "content": system_prompt}
        ] + self.messages
