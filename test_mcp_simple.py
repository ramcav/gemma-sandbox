import asyncio
import subprocess
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_single_server(command, args, server_name):
    print(f"\n=== Testing {server_name} ===")
    print(f"Command: {command} {' '.join(args)}")
    
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=None
    )
    
    try:
        print("Connecting to MCP server...")
        
        # Use the stdio_client directly without AsyncExitStack
        stdio_transport = await asyncio.wait_for(
            stdio_client(server_params).__aenter__(),
            timeout=15.0
        )
        stdio, write = stdio_transport
        
        session = ClientSession(stdio, write)
        await asyncio.wait_for(session.initialize(), timeout=10.0)
        print("✅ Connected successfully!")
        
        # List available tools
        response = await asyncio.wait_for(session.list_tools(), timeout=5.0)
        tools = [tool.name for tool in response.tools]
        print(f"Available tools: {tools}")
        
        # Test a simple tool based on what's available
        if "store" in tools:
            print("Testing store/retrieve...")
            store_result = await asyncio.wait_for(
                session.call_tool("store", {"key": "test", "value": "Hello MCP!"}),
                timeout=10.0
            )
            print(f"✅ Store result: {store_result.content}")
            
            retrieve_result = await asyncio.wait_for(
                session.call_tool("retrieve", {"key": "test"}),
                timeout=10.0
            )
            print(f"✅ Retrieve result: {retrieve_result.content}")
            
        elif "list_directory" in tools:
            print("Testing list_directory...")
            result = await asyncio.wait_for(
                session.call_tool("list_directory", {"path": "/tmp"}),
                timeout=10.0
            )
            print(f"✅ Directory listing result: {result.content}")
            
        elif "execute_query" in tools:
            print("Testing sqlite...")
            result = await asyncio.wait_for(
                session.call_tool("execute_query", {
                    "query": "SELECT 1 as test"
                }),
                timeout=10.0
            )
            print(f"✅ SQLite result: {result.content}")
            
        elif "fetch" in tools:
            print("Testing fetch...")
            result = await asyncio.wait_for(
                session.call_tool("fetch", {"url": "https://httpbin.org/get"}),
                timeout=15.0
            )
            print(f"✅ Fetch result: {result.content[:200]}...")
            
        elif "create_entities" in tools:
            print("Testing knowledge graph...")
            result = await asyncio.wait_for(
                session.call_tool("create_entities", {
                    "entities": [{"name": "test_entity", "entityType": "concept", "observations": ["This is a test"]}]
                }),
                timeout=10.0
            )
            print(f"✅ Knowledge graph result: {result.content}")
            
        else:
            print(f"⚠️  No specific test available for tools: {tools}")
            
        return True
        
    except asyncio.TimeoutError:
        print(f"❌ Timeout connecting to {server_name}")
        return False
    except Exception as e:
        print(f"❌ Error with {server_name}: {e}")
        return False

async def main():
    # Test each server individually
    servers_to_test = [
        # Let's try the knowledge graph server since that's what we're getting
        ("npx", ["-y", "@modelcontextprotocol/server-memory"], "knowledge_graph"),
        
        # Try filesystem
        ("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"], "filesystem"),
        
        # Try sqlite
        ("npx", ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/tmp/test.db"], "sqlite"),
        
        # Try fetch
        ("python", ["-m", "mcp_server_fetch"], "fetch"),
    ]
    
    working_servers = []
    
    for command, args, name in servers_to_test:
        success = await test_single_server(command, args, name)
        if success:
            working_servers.append((command, args, name))
        print("-" * 50)
    
    print(f"\n🎉 Working servers: {[name for _, _, name in working_servers]}")
    
    if working_servers:
        print("\nRecommended configuration:")
        config = {"mcpServers": {}}
        for command, args, name in working_servers:
            config["mcpServers"][name] = {
                "command": command,
                "args": args
            }
        print(json.dumps(config, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 