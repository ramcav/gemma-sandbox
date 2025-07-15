import asyncio
import sys
import os
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
import json
from contextlib import AsyncExitStack

import google.genai as genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Handles MCP server connections and tool management for the Gemma sandbox."""
    
    def __init__(self):
        self.mcp_tools: List[Any] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.tool_to_server: Dict[str, str] = {}  # Add this to track tool -> server mapping
        self.server_resources: Dict[str, Dict[str, Any]] = {}
        self.cached_gemini_declarations: Optional[List[genai_types.FunctionDeclaration]] = None
        self.gemini_tools_dirty: bool = True
        self.status_check_task: Optional[asyncio.Task] = None
        self.active_tools: Set[str] = set()  # Tools that are currently enabled
        
    async def start_monitoring(self):
        """Start the periodic server status monitoring."""
        if not self.status_check_task or self.status_check_task.done():
            self.status_check_task = asyncio.create_task(
                self._periodic_status_checker())
            logger.info("Started periodic server status checker.")
    
    async def stop_monitoring(self):
        """Stop the periodic server status monitoring."""
        if self.status_check_task and not self.status_check_task.done():
            self.status_check_task.cancel()
            try:
                await self.status_check_task
            except asyncio.CancelledError:
                logger.info("Periodic status checker task cancelled.")
            except Exception as e:
                logger.error(f"Error during status checker cleanup: {e}", exc_info=True)
            self.status_check_task = None

    async def _check_server_status(self, identifier: str, session: ClientSession):
        """Check if a server is responsive."""
        try:
            await asyncio.wait_for(session.list_tools(), timeout=5.0)
            if self.server_resources.get(identifier, {}).get('status') == 'error':
                logger.info(f"Server '{identifier}' recovered, setting status to 'connected'.")
                self.server_resources[identifier]['status'] = 'connected'
        except asyncio.TimeoutError:
            logger.warning(f"Server '{identifier}' status check timed out.")
            if self.server_resources.get(identifier, {}).get('status') == 'connected':
                self.server_resources[identifier]['status'] = 'error'
        except Exception as e:
            if self.server_resources.get(identifier, {}).get('status') == 'connected':
                logger.warning(f"Server '{identifier}' became unresponsive: {e}. Setting status to 'error'.")
                self.server_resources[identifier]['status'] = 'error'

    async def _periodic_status_checker(self, interval_seconds: int = 30):
        """Periodically check server status."""
        while True:
            await asyncio.sleep(interval_seconds)
            logger.debug("Running periodic server status check...")
            tasks = []
            active_servers = list(self.server_resources.items())
            for identifier, resources in active_servers:
                if 'session' in resources:
                    tasks.append(self._check_server_status(identifier, resources['session']))
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        try:
                            failed_identifier = active_servers[i][0]
                            logger.error(f"Error during periodic status check for {failed_identifier}: {result}")
                        except IndexError:
                            logger.error(f"Error during periodic status check (index {i}): {result}")

    async def connect_to_mcp_server_from_config(self, server_name: str, config: Dict[str, Any]) -> List[str]:
        """Connect to an MCP server using Claude's configuration format."""
        if server_name in self.server_resources:
            logger.warning(f"Server '{server_name}' is already connected.")
            raise ValueError(f"Server '{server_name}' is already connected.")

        # Extract connection parameters from Claude's format
        command = config.get('command')
        args = config.get('args', [])
        
        if not command:
            raise ValueError(f"Server config for '{server_name}' must have 'command' field")
        
        command_list = [command] + args
        logger.info(f"Connecting to MCP server '{server_name}' with command: {command_list}")

        return await self._connect_with_command_list(server_name, command_list, config)

    async def _connect_with_command_list(self, identifier: str, command_list: List[str], config: Dict[str, Any]) -> List[str]:
        """Internal method to establish MCP server connection."""
        server_params = StdioServerParameters(
            command=command_list[0],
            args=command_list[1:],
            env=None
        )

        server_stack = AsyncExitStack()
        try:
            logger.info(f"Connecting to MCP server: {identifier}")
            logger.info(f"Command: {' '.join(command_list)}")
            
            # Add timeout to server connection
            stdio_transport = await asyncio.wait_for(
                server_stack.enter_async_context(stdio_client(server_params)),
                timeout=30.0
            )
            stdio, write = stdio_transport
            session = await asyncio.wait_for(
                server_stack.enter_async_context(ClientSession(stdio, write)),
                timeout=30.0
            )
            await asyncio.wait_for(session.initialize(), timeout=30.0)
            logger.info(f"Connected to MCP server: {identifier}")

            self.server_resources[identifier] = {
                'session': session,
                'stack': server_stack,
                'tools': [],
                'status': 'connected',
                'command_list': command_list,
                'config': config
            }

            response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            server_tools = response.tools
            logger.info(f"Server {identifier} provides tools: {[tool.name for tool in server_tools]}")

            added_tools_names = []
            for tool in server_tools:
                if tool.name in self.tool_to_session:
                    logger.warning(f"Tool name conflict: '{tool.name}' already exists. Skipping tool from {identifier}.")
                else:
                    self.mcp_tools.append(tool)
                    self.tool_to_session[tool.name] = session
                    self.tool_to_server[tool.name] = identifier  # Add this mapping
                    added_tools_names.append(tool.name)
                    # Auto-enable tools when they're first connected
                    self.active_tools.add(tool.name)
                    self.gemini_tools_dirty = True

            self.server_resources[identifier]['tools'] = added_tools_names
            logger.info(f"Successfully connected to server: {identifier}")
            return added_tools_names

        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to MCP server {identifier}")
            if identifier in self.server_resources:
                res = self.server_resources.pop(identifier)
                await res['stack'].aclose()
            else:
                await server_stack.aclose()
            raise RuntimeError(f"Timeout connecting to MCP server {identifier}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {identifier}: {e}", exc_info=True)
            if identifier in self.server_resources:
                res = self.server_resources.pop(identifier)
                await res['stack'].aclose()
            else:
                await server_stack.aclose()
            raise

    async def disconnect_mcp_server(self, identifier: str) -> bool:
        """Disconnect from an MCP server."""
        if identifier not in self.server_resources:
            logger.warning(f"Attempted to disconnect non-existent server: {identifier}")
            return False

        logger.info(f"Disconnecting MCP server: {identifier}")
        resources = self.server_resources.pop(identifier)
        stack = resources['stack']
        tools_to_remove = resources['tools']

        try:
            await asyncio.wait_for(stack.aclose(), timeout=10.0)
            logger.info(f"Successfully closed resources for server: {identifier}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout closing resources for server {identifier}")
        except Exception as e:
            logger.error(f"Error closing resources for server {identifier}: {e}", exc_info=True)

        # Remove tools from active tools set and mappings
        for tool_name in tools_to_remove:
            self.active_tools.discard(tool_name)
            self.tool_to_server.pop(tool_name, None)  # Remove tool -> server mapping

        self.mcp_tools = [tool for tool in self.mcp_tools if tool.name not in tools_to_remove]
        for tool_name in tools_to_remove:
            self.tool_to_session.pop(tool_name, None)

        if tools_to_remove:
            self.gemini_tools_dirty = True
            logger.info(f"Removed tools from disconnected server {identifier}: {tools_to_remove}")

        return True

    def toggle_tool(self, tool_name: str, enabled: bool):
        """Enable or disable a specific tool."""
        if enabled:
            if tool_name in self.tool_to_session:
                self.active_tools.add(tool_name)
                self.gemini_tools_dirty = True
                logger.info(f"Enabled tool: {tool_name}")
            else:
                logger.warning(f"Cannot enable unknown tool: {tool_name}")
        else:
            if tool_name in self.active_tools:
                self.active_tools.remove(tool_name)
                self.gemini_tools_dirty = True
                logger.info(f"Disabled tool: {tool_name}")

    def get_active_gemini_declarations(self) -> List[genai_types.FunctionDeclaration]:
        """Get Gemini function declarations for only the active tools."""
        if not self.gemini_tools_dirty and self.cached_gemini_declarations is not None:
            # Filter cached declarations by active tools
            return [decl for decl in self.cached_gemini_declarations if decl.name in self.active_tools]

        logger.info("Generating Gemini tool declarations.")
        declarations = []
        type_mapping = {
            'string': 'STRING',
            'number': 'NUMBER',
            'integer': 'INTEGER',
            'boolean': 'BOOLEAN',
            'array': 'ARRAY',
            'object': 'OBJECT',
        }

        # Only process tools that are in active_tools
        active_mcp_tools = [tool for tool in self.mcp_tools if tool.name in self.active_tools]
        
        for mcp_tool in active_mcp_tools:
            try:
                if hasattr(mcp_tool.inputSchema, 'model_dump'):
                    mcp_schema_dict = mcp_tool.inputSchema.model_dump(exclude_none=True)
                elif isinstance(mcp_tool.inputSchema, dict):
                    mcp_schema_dict = mcp_tool.inputSchema
                else:
                    logger.warning(f"MCP tool '{mcp_tool.name}' has unexpected inputSchema type: {type(mcp_tool.inputSchema)}. Skipping.")
                    continue

                if mcp_schema_dict.get('type', '').lower() != 'object':
                    logger.warning(f"MCP tool '{mcp_tool.name}' has non-OBJECT inputSchema. Skipping for Gemini.")
                    continue

                gemini_properties = {}
                required_props = mcp_schema_dict.get('required', [])
                valid_properties_found = False

                for prop_name, prop_schema_dict in mcp_schema_dict.get('properties', {}).items():
                    if not isinstance(prop_schema_dict, dict):
                        logger.warning(f"Property '{prop_name}' in tool '{mcp_tool.name}' has non-dict schema. Skipping property.")
                        continue

                    mcp_type = prop_schema_dict.get('type', '').lower()
                    gemini_type_str = type_mapping.get(mcp_type)

                    if mcp_type == 'object' and not prop_schema_dict.get('properties'):
                        logger.warning(f"Property '{prop_name}' in tool '{mcp_tool.name}' is MCP type 'object' with no sub-properties. Mapping to Gemini STRING type.")
                        gemini_type_str = 'STRING'

                    if gemini_type_str:
                        description = prop_schema_dict.get('description', '')
                        if gemini_type_str == 'STRING' and mcp_type == 'object':
                            description += " (Provide as JSON string)"

                        gemini_properties[prop_name] = genai_types.Schema(
                            type=gemini_type_str,
                            description=description.strip() or None
                        )
                        valid_properties_found = True
                    else:
                        logger.warning(f"Property '{prop_name}' in tool '{mcp_tool.name}' has unmappable MCP type '{mcp_type}'. Skipping property.")

                if valid_properties_found or not mcp_schema_dict.get('properties'):
                    gemini_params_schema = genai_types.Schema(
                        type='OBJECT',
                        properties=gemini_properties if gemini_properties else None,
                        required=required_props if required_props and gemini_properties else None
                    )

                    declaration = genai_types.FunctionDeclaration(
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        parameters=gemini_params_schema,
                    )
                    declarations.append(declaration)
                else:
                    logger.warning(f"Skipping tool '{mcp_tool.name}' for Gemini: No valid properties could be mapped.")

            except Exception as e:
                logger.error(f"Failed to convert MCP tool '{mcp_tool.name}' to Gemini declaration: {e}. Skipping this tool.", exc_info=True)
                continue

        self.cached_gemini_declarations = declarations
        self.gemini_tools_dirty = False
        logger.info(f"Generated {len(declarations)} active Gemini tool declarations.")
        return declarations

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Execute an MCP tool and return status and content."""
        if tool_name not in self.tool_to_session:
            logger.error(f"Attempted to call unknown or disconnected MCP tool: {tool_name}")
            error_msg = f"Error: Tool '{tool_name}' not found or its server is disconnected."
            return error_msg, None

        if tool_name not in self.active_tools:
            logger.error(f"Attempted to call disabled MCP tool: {tool_name}")
            error_msg = f"Error: Tool '{tool_name}' is currently disabled."
            return error_msg, None

        session = self.tool_to_session[tool_name]
        # Use the direct mapping instead of searching through all servers
        server_identifier = self.tool_to_server.get(tool_name)

        if not server_identifier:
            logger.error(f"Could not find server identifier for tool '{tool_name}'.")
            error_msg = f"Error: Internal error finding server for tool '{tool_name}'."
            return error_msg, None

        try:
            logger.info(f"Executing MCP tool '{tool_name}' with args: {args}")
            logger.info(f"Tool '{tool_name}' is on server '{server_identifier}'")
            
            # Add timeout to tool execution with progress logging
            start_time = asyncio.get_event_loop().time()
            
            # Create a task for the tool execution
            tool_task = asyncio.create_task(session.call_tool(tool_name, args))
            
            # Create a task for periodic progress logging
            async def log_progress():
                while not tool_task.done():
                    await asyncio.sleep(5)  # Log every 5 seconds
                    if not tool_task.done():
                        elapsed = asyncio.get_event_loop().time() - start_time
                        logger.info(f"Tool '{tool_name}' still executing... ({elapsed:.1f}s elapsed)")
            
            progress_task = asyncio.create_task(log_progress())
            
            try:
                # Wait for the tool execution with timeout
                response = await asyncio.wait_for(tool_task, timeout=30.0)  # Reduced timeout to 30s
                progress_task.cancel()
                
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"MCP tool '{tool_name}' executed successfully in {elapsed:.1f}s")
                
                if self.server_resources[server_identifier]['status'] == 'error':
                    logger.info(f"Server '{server_identifier}' recovered, setting status to 'connected'.")
                    self.server_resources[server_identifier]['status'] = 'connected'
                
                result_content = str(response.content) if response.content is not None else ""
                logger.info(f"Tool '{tool_name}' returned {len(result_content)} characters")
                return "Success", result_content
                
            except asyncio.TimeoutError:
                progress_task.cancel()
                tool_task.cancel()
                logger.error(f"Timeout executing MCP tool '{tool_name}' on server '{server_identifier}' (30s timeout)")
                if server_identifier:
                    self.server_resources[server_identifier]['status'] = 'error'
                error_msg = f"Timeout executing tool '{tool_name}' (30s timeout exceeded)"
                return error_msg, None
            
        except Exception as e:
            logger.error(f"Error executing MCP tool '{tool_name}' on server '{server_identifier}': {e}", exc_info=True)
            if server_identifier:
                self.server_resources[server_identifier]['status'] = 'error'
            error_msg = f"Error executing tool '{tool_name}': {e}"
            return error_msg, None

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get a list of all available tools with their metadata."""
        tools = []
        for tool in self.mcp_tools:
            tools.append({
                'name': tool.name,
                'description': tool.description,
                'enabled': tool.name in self.active_tools,
                'server': self.tool_to_server.get(tool.name, 'Unknown')  # Use direct mapping
            })
        return tools

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all connected servers."""
        status = {}
        for identifier, resources in self.server_resources.items():
            status[identifier] = {
                'status': resources['status'],
                'tools': resources['tools'],
                'config': resources.get('config', {})
            }
        return status

    async def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up MCP client resources...")
        await self.stop_monitoring()
        
        server_identifiers = list(self.server_resources.keys())
        for identifier in server_identifiers:
            await self.disconnect_mcp_server(identifier)
        
        logger.info("MCP client cleanup complete.") 