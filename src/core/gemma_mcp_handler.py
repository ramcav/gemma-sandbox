import google.genai as genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from typing import List, Dict, Any, Optional, Tuple
import logging
import asyncio
import ollama

from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class GemmaMCPHandler:
    """Handles Gemma model integration with MCP tools for both online and offline models."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash", is_local: bool = False):
        self.api_key = api_key
        self.model_name = model_name
        self.is_local = is_local
        self.client: Optional[genai.Client] = None
        self.async_client = None
        self.mcp_client = MCPClient()
        self.chat_history: List[genai_types.Content] = []
        
        # Model definitions matching your original structure
        self.online_models = {
            "GEMINI_2.5": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "GEMINI_2.0": ["gemini-2.0-flash", "gemini-2.0-flash-lite"],
            "GEMMA": [
                "gemma-3n-e4b-it", "gemma-3-1b-it", "gemma-3-4b-it",
                "gemma-3-12b-it", "gemma-3-27b-it"
            ],
            "OTHER": ["learnlm-2.0-flash-experimental"]
        }
        
        self.local_models = ["gemma3n:latest"]
        
        # Flatten online models for validation
        self.available_online_models = [
            model for models in self.online_models.values() for model in models
        ]
    
    async def initialize(self):
        """Initialize the appropriate client and MCP monitoring."""
        try:
            if not self.is_local:
                # Online model initialization
                if not self.api_key:
                    raise ValueError("API key is required for online models")
                
                # Use the correct way to initialize the client
                self.client = genai.Client(api_key=self.api_key)
                self.async_client = self.client.aio
                logger.info(f"Online Gemini client initialized with model: {self.model_name}")
            else:
                # Local model initialization - just validate the model exists
                try:
                    # Test if Ollama is running and model is available
                    ollama.list()
                    logger.info(f"Local Ollama client initialized with model: {self.model_name}")
                except Exception as e:
                    raise RuntimeError(f"Ollama not available or model not found: {e}")
            
            await self.mcp_client.start_monitoring()
            logger.info("Gemma MCP handler initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemma MCP handler: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources."""
        await self.mcp_client.cleanup()
    
    def set_model(self, model_name: str, is_local: bool = False):
        """Set the model to use."""
        if is_local:
            if model_name not in self.local_models:
                raise ValueError(f"Local model {model_name} not supported. Available: {self.local_models}")
        else:
            if model_name not in self.available_online_models:
                raise ValueError(f"Online model {model_name} not supported. Available: {self.available_online_models}")
        
        self.model_name = model_name
        self.is_local = is_local
        logger.info(f"Switched to {'local' if is_local else 'online'} model: {model_name}")
    
    def clear_history(self):
        """Clear the chat history."""
        self.chat_history = []
        logger.info("Chat history cleared.")
    
    async def connect_mcp_server(self, server_name: str, config: Dict[str, Any]) -> List[str]:
        """Connect to an MCP server using Claude's configuration format."""
        return await self.mcp_client.connect_to_mcp_server_from_config(server_name, config)
    
    async def disconnect_mcp_server(self, identifier: str) -> bool:
        """Disconnect from an MCP server."""
        return await self.mcp_client.disconnect_mcp_server(identifier)
    
    def toggle_tool(self, tool_name: str, enabled: bool):
        """Enable or disable a tool."""
        self.mcp_client.toggle_tool(tool_name, enabled)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.mcp_client.get_available_tools()
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get server status information."""
        return self.mcp_client.get_server_status()
    
    def get_online_models(self) -> Dict[str, List[str]]:
        """Get available online models."""
        return self.online_models
    
    def get_local_models(self) -> List[str]:
        """Get available local models."""
        return self.local_models
    
    async def _process_online_message(self, message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Process message using online Gemini API."""
        tool_call_log = []
        
        # Add user message to history
        self.chat_history.append(genai_types.Content(
            role="user", 
            parts=[genai_types.Part(text=message)]
        ))
        
        try:
            # Get active tool declarations
            gemini_declarations = self.mcp_client.get_active_gemini_declarations()
            gemini_tools = [genai_types.Tool(function_declarations=gemini_declarations)] if gemini_declarations else None
            config = genai_types.GenerateContentConfig(tools=gemini_tools) if gemini_tools else None
            
            logger.info(f"Processing message with {len(gemini_declarations) if gemini_declarations else 0} active tools")
            
            # Generate initial response
            response = await self.async_client.models.generate_content(
                model=self.model_name,
                contents=self.chat_history,
                config=config
            )
            
            if not response.candidates or not response.candidates[0].content:
                # Handle blocked or empty responses
                feedback = getattr(response, 'prompt_feedback', None)
                if feedback and getattr(feedback, 'block_reason', None):
                    error_msg = f"Response blocked: {feedback.block_reason}"
                    if hasattr(feedback, 'block_reason_message'):
                        error_msg += f" - {feedback.block_reason_message}"
                    self.chat_history.pop()  # Remove user message
                    return error_msg, tool_call_log
                
                self.chat_history.pop()
                return "Error: No response content from model.", tool_call_log
            
            model_content = response.candidates[0].content
            if not model_content.parts:
                self.chat_history.pop()
                return "Error: Empty response from model.", tool_call_log
            
            self.chat_history.append(model_content)
            
            # Check for function calls
            function_calls = [
                part.function_call for part in model_content.parts 
                if hasattr(part, 'function_call') and part.function_call
            ]
            
            if function_calls:
                logger.info(f"Model requested {len(function_calls)} tool calls")
                tool_response_parts = []
                
                for function_call in function_calls:
                    tool_name = function_call.name
                    tool_args = dict(function_call.args)
                    
                    # Log tool call start
                    tool_call_log.append({
                        'type': 'start',
                        'tool': tool_name,
                        'args': tool_args
                    })
                    
                    # Execute tool
                    status, content = await self.mcp_client.execute_tool(tool_name, tool_args)
                    
                    # Log tool call end
                    tool_call_log.append({
                        'type': 'end',
                        'tool': tool_name,
                        'status': status,
                        'content': content if status == "Success" else None,
                        'error': status if status != "Success" else None
                    })
                    
                    # Prepare response for Gemini
                    result_content = content if status == "Success" else status
                    tool_response_parts.append(
                        genai_types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result_content}
                        )
                    )
                
                if tool_response_parts:
                    # Add tool responses to history
                    self.chat_history.append(genai_types.Content(
                        role="tool",
                        parts=tool_response_parts
                    ))
                    
                    # Get final response after tool execution
                    final_response = await self.async_client.models.generate_content(
                        model=self.model_name,
                        contents=self.chat_history,
                        config=config
                    )
                    
                    if not final_response.candidates or not final_response.candidates[0].content:
                        # Clean up history on error
                        if len(self.chat_history) >= 2:
                            self.chat_history.pop()  # Remove tool response
                            self.chat_history.pop()  # Remove model response
                        return "Error: No response after tool execution.", tool_call_log
                    
                    final_content = final_response.candidates[0].content
                    if not final_content.parts:
                        if len(self.chat_history) >= 2:
                            self.chat_history.pop()
                            self.chat_history.pop()
                        return "Error: Empty response after tool execution.", tool_call_log
                    
                    self.chat_history.append(final_content)
                    
                    if final_content.parts and hasattr(final_content.parts[0], 'text'):
                        return final_content.parts[0].text, tool_call_log
                    else:
                        return "Tool execution completed but no text response received.", tool_call_log
            
            # No function calls, return direct text response
            elif model_content.parts and hasattr(model_content.parts[0], 'text'):
                return model_content.parts[0].text, tool_call_log
            else:
                return "Received response with no text content.", tool_call_log
                
        except genai_errors.APIError as e:
            self.chat_history.pop()  # Remove user message on error
            logger.error(f"Gemini API error: {e}")
            return f"API Error: {e.message}", tool_call_log
        except Exception as e:
            self.chat_history.pop()
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Unexpected error: {e}", tool_call_log
    
    async def _process_local_message(self, message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Process message using local Ollama model."""
        tool_call_log = []
        
        # For local models, we need to simulate the conversation format
        # Convert chat history to Ollama format
        messages = []
        for content in self.chat_history:
            if content.role == "user":
                messages.append({"role": "user", "content": content.parts[0].text})
            elif content.role == "model":
                messages.append({"role": "assistant", "content": content.parts[0].text})
        
        # Add new user message
        messages.append({"role": "user", "content": message})
        
        try:
            # Get available tools for context (even though Ollama doesn't support function calling directly)
            available_tools = self.mcp_client.get_available_tools()
            active_tools = [tool for tool in available_tools if tool['enabled']]
            
            # Create a system prompt that includes tool information
            system_prompt = "You are a helpful assistant."
            if active_tools:
                tool_descriptions = []
                for tool in active_tools:
                    tool_descriptions.append(f"- {tool['name']}: {tool['description']}")
                
                system_prompt += f"\n\nYou have access to the following tools:\n" + "\n".join(tool_descriptions)
                system_prompt += "\n\nTo use a tool, respond with: TOOL_CALL: tool_name(arg1=value1, arg2=value2)"
            
            # Add system message
            ollama_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Generate response
            response = ollama.chat(model=self.model_name, messages=ollama_messages)
            response_text = response['message']['content']
            
            # Check if response contains tool calls (simple parsing)
            if "TOOL_CALL:" in response_text:
                # Extract tool calls (simplified - you might want more robust parsing)
                lines = response_text.split('\n')
                tool_calls = []
                response_parts = []
                
                for line in lines:
                    if line.strip().startswith("TOOL_CALL:"):
                        # Parse tool call - this is a simplified parser
                        tool_part = line.replace("TOOL_CALL:", "").strip()
                        if '(' in tool_part and ')' in tool_part:
                            tool_name = tool_part.split('(')[0].strip()
                            args_str = tool_part.split('(')[1].split(')')[0]
                            
                            # Simple argument parsing (you might want more robust parsing)
                            args = {}
                            if args_str:
                                for arg in args_str.split(','):
                                    if '=' in arg:
                                        key, value = arg.split('=', 1)
                                        args[key.strip()] = value.strip().strip('"\'')
                            
                            tool_calls.append((tool_name, args))
                    else:
                        response_parts.append(line)
                
                # Execute tool calls
                tool_results = []
                for tool_name, tool_args in tool_calls:
                    # Log tool call start
                    tool_call_log.append({
                        'type': 'start',
                        'tool': tool_name,
                        'args': tool_args
                    })
                    
                    # Execute tool
                    status, content = await self.mcp_client.execute_tool(tool_name, tool_args)
                    
                    # Log tool call end
                    tool_call_log.append({
                        'type': 'end',
                        'tool': tool_name,
                        'status': status,
                        'content': content if status == "Success" else None,
                        'error': status if status != "Success" else None
                    })
                    
                    tool_results.append(f"Tool {tool_name} result: {content if status == 'Success' else status}")
                
                # Combine response with tool results
                final_response = '\n'.join(response_parts).strip()
                if tool_results:
                    final_response += '\n\n' + '\n'.join(tool_results)
                
                # Update chat history
                self.chat_history.append(genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=message)]
                ))
                self.chat_history.append(genai_types.Content(
                    role="model",
                    parts=[genai_types.Part(text=final_response)]
                ))
                
                return final_response, tool_call_log
            else:
                # No tool calls, regular response
                self.chat_history.append(genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=message)]
                ))
                self.chat_history.append(genai_types.Content(
                    role="model",
                    parts=[genai_types.Part(text=response_text)]
                ))
                
                return response_text, tool_call_log
                
        except Exception as e:
            logger.error(f"Error processing local message: {e}", exc_info=True)
            return f"Error with local model: {e}", tool_call_log
    
    async def process_message(self, message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a user message and return the response and tool call log.
        
        Returns:
            Tuple of (response_text, tool_call_log)
        """
        if self.is_local:
            return await self._process_local_message(message)
        else:
            if not self.async_client:
                raise RuntimeError("Handler not initialized. Call initialize() first.")
            return await self._process_online_message(message) 