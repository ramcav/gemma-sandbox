import google.generativeai as genai
import os
from typing import Any
from .llm_handler import LLMHandler

class OnlineHandler(LLMHandler):
    """
    Handles chat logic for online models using Google AI Studio.
    Inherits shared functionality from LLMHandler.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for online mode")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def _call_model(self, system_prompt: str) -> str:
        """Call Google Gemini with the prepared messages"""
        messages = self._prepare_messages_for_model(system_prompt)
        
        print("🤔 Thinking...")
        
        response = self.model.generate_content(
            messages,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        return response.text

    def _prepare_messages_for_model(self, system_prompt: str) -> str:
        """Format messages for Gemini's expected format"""
        
        full_prompt = f"{system_prompt}\n\nConversation history:\n"
        
        for msg in self.messages:
            if msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Assistant: {msg['content']}\n"
        
        full_prompt += "\nPlease respond with JSON according to the instructions above."
        
        return full_prompt
