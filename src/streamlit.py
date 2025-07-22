import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Gemma MCP Sandbox",
    page_icon="🤖",
    layout="wide"
)

# --- Model Definitions ---
ONLINE_MODELS = {
    "GEMINI_2.5": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "GEMINI_2.0": ["gemini-2.0-flash", "gemini-2.0-flash-lite"],
    "GEMMA": [
        "gemma-3n-e4b-it", "gemma-3-1b-it", "gemma-3-4b-it",
        "gemma-3-12b-it", "gemma-3-27b-it"
    ],
    "OTHER": ["learnlm-2.0-flash-experimental"]
}

# Flatten the dictionary for the selectbox, formatting the options
online_model_options = [
    f"{category} / {model}"
    for category, models in ONLINE_MODELS.items()
    for model in models
]

LOCAL_MODELS = ["gemma3n:latest"]

# # Initialize session state
# if "mcp_handler" not in st.session_state:
#     st.session_state.mcp_handler = None
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "tool_call_log" not in st.session_state:
#     st.session_state.tool_call_log = []
# if "config_manager" not in st.session_state:
#     st.session_state.config_manager = MCPConfigManager()
# if "show_config_editor" not in st.session_state:
#     st.session_state.show_config_editor = False
# if "config_editor_content" not in st.session_state:
#     st.session_state.config_editor_content = ""

# # Async wrapper for running async functions in Streamlit
# def run_async(coro):
#     """Run an async coroutine in Streamlit."""
#     try:
#         loop = asyncio.get_event_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
    
#     return loop.run_until_complete(coro)

# # Sidebar configuration
# with st.sidebar:
#     st.title("⚙️ MCP Sandbox Configuration")
    
#     # Model and API configuration
#     st.header("🤖 Model Configuration")
    
#     # Toggle between local and online
#     run_local = st.toggle("Run Local", value=False)
    
#     selected_model = None
#     api_key = None
    
#     if run_local:
#         st.subheader("Local Model (Ollama)")
#         selected_model = st.selectbox(
#             "Select a local model",
#             LOCAL_MODELS
#         )
#     else:
#         st.subheader("Online Model (Google AI Studio)")
#         api_key = st.text_input(
#             "GEMINI_API_KEY",
#             type="password",
#             help="Paste your Google AI Studio API Key here.",
#             value=os.getenv("GEMINI_API_KEY", "")
#         )
        
#         # Extract the model name from the formatted string
#         formatted_model = st.selectbox(
#             "Select an online model",
#             online_model_options
#         )
#         if formatted_model:
#             selected_model = formatted_model.split(" / ")[1]
    
#     # Context Management on Model Change
#     if 'active_model_info' not in st.session_state:
#         st.session_state.active_model_info = {
#             "model": selected_model,
#             "is_local": run_local
#         }

#     # Check if the model or mode has been changed by the user
#     model_changed = st.session_state.active_model_info["model"] != selected_model
#     mode_changed = st.session_state.active_model_info["is_local"] != run_local

#     if model_changed or mode_changed:
#         st.warning("Model or mode has changed. For a clean slate, clear the chat history.")
#         if st.button("Clear Chat History", use_container_width=True, key="clear_chat"):
#             # Clear the messages
#             st.session_state.messages = []
#             st.session_state.tool_call_log = []
#             # Update the tracker to the new model/mode
#             st.session_state.active_model_info = {
#                 "model": selected_model,
#                 "is_local": run_local
#             }
#             # Clear handler to force reinitialization
#             if st.session_state.mcp_handler:
#                 run_async(st.session_state.mcp_handler.cleanup())
#                 st.session_state.mcp_handler = None
#             logging.info("Chat history cleared due to model change.")
#             st.rerun()
    
#     # Initialize or update handler
#     should_initialize = (
#         selected_model and 
#         (st.session_state.mcp_handler is None or 
#          st.session_state.get("current_api_key") != api_key or
#          st.session_state.get("current_model") != selected_model or
#          st.session_state.get("current_is_local") != run_local)
#     )
    
#     if should_initialize:
#         if not run_local and not api_key:
#             st.error("❌ Please enter your GEMINI_API_KEY to use online models.")
#         else:
#             try:
#                 if st.session_state.mcp_handler:
#                     run_async(st.session_state.mcp_handler.cleanup())
                
#                 st.session_state.mcp_handler = GemmaMCPHandler(
#                     api_key=api_key, 
#                     model_name=selected_model, 
#                     is_local=run_local
#                 )
#                 run_async(st.session_state.mcp_handler.initialize())
#                 st.session_state.current_api_key = api_key
#                 st.session_state.current_model = selected_model
#                 st.session_state.current_is_local = run_local
#                 st.success("✅ Model initialized successfully!")
#             except Exception as e:
#                 st.error(f"❌ Failed to initialize model: {e}")
#                 st.session_state.mcp_handler = None
    
#     st.divider()
    
#     # MCP Server Management
#     st.header("🔧 MCP Server Management")
    
#     # Main button to edit MCP servers configuration
#     if st.button("📝 Edit MCP Servers Configuration", use_container_width=True):
#         st.session_state.show_config_editor = True
#         st.session_state.config_editor_content = st.session_state.config_manager.get_raw_config()
#         st.rerun()
    
#     # Show sample configuration button
#     if st.button("📋 Show Sample Configuration", use_container_width=True):
#         st.session_state.show_config_editor = True
#         st.session_state.config_editor_content = st.session_state.config_manager.get_sample_config()
#         st.rerun()
    
#     # Server connection management
#     if st.session_state.mcp_handler:
#         st.subheader("📡 Server Connections")
        
#         available_configs = st.session_state.config_manager.get_all_configs()
#         server_status = st.session_state.mcp_handler.get_server_status()
        
#         if available_configs:
#             for server_name, config in available_configs.items():
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     is_connected = server_name in server_status
#                     status_icon = "🟢" if is_connected else "🔴"
#                     st.write(f"{status_icon} **{server_name}**")
#                     st.caption(f"Command: {config.get('command', 'N/A')}")
#                     if config.get('args'):
#                         st.caption(f"Args: {' '.join(config['args'])}")
                
#                 with col2:
#                     if is_connected:
#                         if st.button("Disconnect", key=f"disconnect_{server_name}"):
#                             try:
#                                 success = run_async(st.session_state.mcp_handler.disconnect_mcp_server(server_name))
#                                 if success:
#                                     st.success(f"Disconnected from {server_name}")
#                                     st.rerun()
#                                 else:
#                                     st.error(f"Failed to disconnect from {server_name}")
#                             except Exception as e:
#                                 st.error(f"Error disconnecting: {e}")
#                     else:
#                         if st.button("Connect", key=f"connect_{server_name}"):
#                             try:
#                                 tools = run_async(st.session_state.mcp_handler.connect_mcp_server(server_name, config))
#                                 st.success(f"Connected to {server_name}, found {len(tools)} tools")
#                                 st.rerun()
#                             except Exception as e:
#                                 st.error(f"Failed to connect: {e}")
#         else:
#             st.info("No MCP servers configured. Click 'Edit MCP Servers Configuration' to add servers.")
    
#     st.divider()
    
#     # Tool Management
#     if st.session_state.mcp_handler:
#         st.header("🛠️ Tool Management")
        
#         available_tools = st.session_state.mcp_handler.get_available_tools()
        
#         if available_tools:
#             st.subheader("Available Tools")
            
#             for tool in available_tools:
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     st.write(f"**{tool['name']}**")
#                     st.caption(f"Server: {tool['server']}")
#                     if tool['description']:
#                         st.caption(tool['description'])
                
#                 with col2:
#                     current_state = tool['enabled']
#                     new_state = st.checkbox(
#                         "Enabled",
#                         value=current_state,
#                         key=f"tool_{tool['name']}"
#                     )
                    
#                     if new_state != current_state:
#                         st.session_state.mcp_handler.toggle_tool(tool['name'], new_state)
#                         if new_state:
#                             st.success(f"Enabled {tool['name']}")
#                         else:
#                             st.info(f"Disabled {tool['name']}")
#                         st.rerun()
#         else:
#             st.info("No tools available. Connect to MCP servers to access tools.")
    
#     # Clear chat button
#     if st.button("🗑️ Clear Chat History", use_container_width=True):
#         st.session_state.messages = []
#         st.session_state.tool_call_log = []
#         if st.session_state.mcp_handler:
#             st.session_state.mcp_handler.clear_history()
#         st.success("Chat history cleared!")
#         st.rerun()

# # Configuration Editor Modal
# if st.session_state.show_config_editor:
#     st.title("📝 MCP Servers Configuration Editor")
    
#     st.info("Edit the MCP servers configuration below. This follows Claude's format.")
    
#     # Text area for editing the configuration
#     config_content = st.text_area(
#         "Configuration (JSON)",
#         value=st.session_state.config_editor_content,
#         height=400,
#         help="Edit the MCP servers configuration in JSON format"
#     )
    
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         if st.button("💾 Save Configuration", use_container_width=True):
#             if st.session_state.config_manager.set_raw_config(config_content):
#                 st.success("✅ Configuration saved successfully!")
#                 st.session_state.show_config_editor = False
                
#                 # Disconnect any servers that are no longer in the config
#                 if st.session_state.mcp_handler:
#                     current_servers = set(st.session_state.mcp_handler.get_server_status().keys())
#                     new_servers = set(st.session_state.config_manager.get_all_configs().keys())
#                     servers_to_disconnect = current_servers - new_servers
                    
#                     for server_name in servers_to_disconnect:
#                         try:
#                             run_async(st.session_state.mcp_handler.disconnect_mcp_server(server_name))
#                             st.info(f"Disconnected removed server: {server_name}")
#                         except Exception as e:
#                             st.error(f"Error disconnecting {server_name}: {e}")
                
#                 st.rerun()
#             else:
#                 st.error("❌ Failed to save configuration. Please check the JSON format.")
    
#     with col2:
#         if st.button("❌ Cancel", use_container_width=True):
#             st.session_state.show_config_editor = False
#             st.rerun()
    
#     with col3:
#         if st.button("🔄 Reset to Current", use_container_width=True):
#             st.session_state.config_editor_content = st.session_state.config_manager.get_raw_config()
#             st.rerun()
    
#     st.divider()
    
#     # Help section
#     with st.expander("💡 Configuration Help", expanded=False):
#         st.markdown("""
#         ### MCP Servers Configuration Format
        
#         The configuration follows Claude's format:
        
#         ```json
#         {
#           "mcpServers": {
#             "server_name": {
#               "command": "command_to_run",
#               "args": ["arg1", "arg2", "arg3"]
#             }
#           }
#         }
#         ```
        
#         ### Examples:
        
#         **Fetch Server (uvx)**:
#         ```json
#         {
#           "mcpServers": {
#             "fetch": {
#               "command": "uvx",
#               "args": ["mcp-server-fetch"]
#             }
#           }
#         }
#         ```
        
#         **Filesystem Server (npx)**:
#         ```json
#         {
#           "mcpServers": {
#             "filesystem": {
#               "command": "npx",
#               "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
#             }
#           }
#         }
#         ```
        
#         **Multiple Servers**:
#         ```json
#         {
#           "mcpServers": {
#             "fetch": {
#               "command": "uvx",
#               "args": ["mcp-server-fetch"]
#             },
#             "brave_search": {
#               "command": "uvx",
#               "args": ["mcp-server-brave-search"]
#             }
#           }
#         }
#         ```
#         """)

# # Main chat interface (only show if not in config editor mode)
# if not st.session_state.show_config_editor:
#     col1, col2 = st.columns([2, 1])

#     with col1:
#         st.title("Gemma MCP Sandbox")
#         st.caption("Chat with Gemma using MCP tools")
        
#         # Display current model info
#         if st.session_state.mcp_handler:
#             model_info = f"{'🖥️ Local' if run_local else '☁️ Online'}: {selected_model}"
#             st.info(model_info)
        
#         # Display chat messages
#         for message in st.session_state.messages:
#             with st.chat_message(message["role"]):
#                 st.markdown(message["content"])
        
#         # Chat input
#         if prompt := st.chat_input("What can I help you with?"):
#             if not st.session_state.mcp_handler:
#                 st.error("Please configure your model first.")
#             else:
#                 # Add user message
#                 st.session_state.messages.append({"role": "user", "content": prompt})
#                 with st.chat_message("user"):
#                     st.markdown(prompt)
                
#                 # Process with MCP handler
#                 with st.chat_message("assistant"):
#                     with st.spinner("Thinking..."):
#                         try:
#                             response, tool_calls = run_async(
#                                 st.session_state.mcp_handler.process_message(prompt)
#                             )
#                             st.markdown(response)
#                             st.session_state.messages.append({"role": "assistant", "content": response})
#                             st.session_state.tool_call_log.extend(tool_calls)
#                         except Exception as e:
#                             error_msg = f"Error: {e}"
#                             st.error(error_msg)
#                             st.session_state.messages.append({"role": "assistant", "content": error_msg})

#     with col2:
#         st.subheader("🔧 Tool Call Log")
        
#         if st.session_state.tool_call_log:
#             # Show recent tool calls
#             recent_calls = st.session_state.tool_call_log[-10:]  # Last 10 calls
            
#             for i, call in enumerate(reversed(recent_calls)):
#                 if call['type'] == 'start':
#                     with st.expander(f"🔧 {call['tool']}", expanded=i < 3):
#                         st.write("**Arguments:**")
#                         st.json(call['args'])
#                 elif call['type'] == 'end':
#                     status_icon = "✅" if call['status'] == 'Success' else "❌"
#                     with st.expander(f"{status_icon} {call['tool']} - {call['status']}", expanded=i < 3):
#                         if call['status'] == 'Success' and call['content']:
#                             st.write("**Result:**")
#                             st.text(call['content'][:500] + "..." if len(call['content']) > 500 else call['content'])
#                         elif call['error']:
#                             st.write("**Error:**")
#                             st.error(call['error'])
            
#             if st.button("Clear Tool Log"):
#                 st.session_state.tool_call_log = []
#                 st.rerun()
#         else:
#             st.info("No tool calls yet. Tools will appear here when the AI uses them.")