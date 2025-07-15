import json
import os
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """Manages MCP server configurations in Claude's format."""
    
    def __init__(self, config_file: str = "src/mcp_servers.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {"mcpServers": {}}
        self.load_config()
    
    def load_config(self):
        """Load MCP server configurations from JSON file."""
        if not os.path.exists(self.config_file):
            logger.info(f"Config file {self.config_file} not found, creating default config.")
            self.config = {"mcpServers": {}}
            self.save_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read().strip()
                if content:
                    loaded_config = json.loads(content)
                    # Handle both old format and new format
                    if "mcpServers" in loaded_config:
                        self.config = loaded_config
                    else:
                        # Convert old format to new format
                        self.config = {"mcpServers": loaded_config}
                else:
                    self.config = {"mcpServers": {}}
            logger.info(f"Loaded {len(self.config['mcpServers'])} MCP server configurations.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file {self.config_file}: {e}")
            self.config = {"mcpServers": {}}
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            self.config = {"mcpServers": {}}
    
    def save_config(self):
        """Save MCP server configurations to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved {len(self.config['mcpServers'])} MCP server configurations.")
        except Exception as e:
            logger.error(f"Failed to save config file {self.config_file}: {e}")
    
    def get_raw_config(self) -> str:
        """Get the raw JSON configuration as a string."""
        return json.dumps(self.config, indent=2)
    
    def set_raw_config(self, config_str: str) -> bool:
        """Set the configuration from a raw JSON string."""
        try:
            new_config = json.loads(config_str)
            
            # Validate the structure
            if not isinstance(new_config, dict):
                logger.error("Config must be a JSON object")
                return False
            
            if "mcpServers" not in new_config:
                logger.error("Config must contain 'mcpServers' key")
                return False
            
            if not isinstance(new_config["mcpServers"], dict):
                logger.error("'mcpServers' must be an object")
                return False
            
            # Validate each server configuration
            for server_name, server_config in new_config["mcpServers"].items():
                if not self._validate_server_config(server_name, server_config):
                    return False
            
            self.config = new_config
            self.save_config()
            logger.info(f"Updated configuration with {len(self.config['mcpServers'])} servers.")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting config: {e}")
            return False
    
    def add_server_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a new MCP server configuration."""
        if name in self.config["mcpServers"]:
            logger.warning(f"Server config '{name}' already exists.")
            return False
        
        if not self._validate_server_config(name, config):
            return False
        
        self.config["mcpServers"][name] = config
        self.save_config()
        logger.info(f"Added MCP server config: {name}")
        return True
    
    def update_server_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Update an existing MCP server configuration."""
        if name not in self.config["mcpServers"]:
            logger.warning(f"Server config '{name}' not found.")
            return False
        
        if not self._validate_server_config(name, config):
            return False
        
        self.config["mcpServers"][name] = config
        self.save_config()
        logger.info(f"Updated MCP server config: {name}")
        return True
    
    def remove_server_config(self, name: str) -> bool:
        """Remove an MCP server configuration."""
        if name not in self.config["mcpServers"]:
            logger.warning(f"Server config '{name}' not found.")
            return False
        
        del self.config["mcpServers"][name]
        self.save_config()
        logger.info(f"Removed MCP server config: {name}")
        return True
    
    def get_server_config(self, name: str) -> Dict[str, Any]:
        """Get a specific server configuration."""
        return self.config["mcpServers"].get(name, {})
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all server configurations."""
        return self.config["mcpServers"].copy()
    
    def _validate_server_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Validate a server configuration."""
        if not isinstance(config, dict):
            logger.error(f"Server config for '{name}' must be an object")
            return False
        
        if "command" not in config:
            logger.error(f"Server config for '{name}' must have 'command' field")
            return False
        
        if not isinstance(config["command"], str):
            logger.error(f"'command' for server '{name}' must be a string")
            return False
        
        if "args" in config and not isinstance(config["args"], list):
            logger.error(f"'args' for server '{name}' must be a list")
            return False
        
        # Ensure args is a list of strings
        if "args" in config:
            for arg in config["args"]:
                if not isinstance(arg, str):
                    logger.error(f"All args for server '{name}' must be strings")
                    return False
        
        return True
    
    def get_sample_config(self) -> str:
        """Get a sample configuration in Claude's format."""
        sample = {
            "mcpServers": {
                "fetch_uvx": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"]
                },
                "fetch_pip": {
                    "command": "python",
                    "args": ["-m", "mcp_server_fetch"]
                },
                "fetch_docker": {
                    "command": "docker",
                    "args": ["run", "-i", "--rm", "mcp/fetch"]
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
                },
                "brave_search": {
                    "command": "uvx",
                    "args": ["mcp-server-brave-search"]
                },
                "postgres": {
                    "command": "uvx",
                    "args": ["mcp-server-postgres", "--connection-string", "postgresql://user:password@localhost:5432/dbname"]
                }
            }
        }
        return json.dumps(sample, indent=2) 