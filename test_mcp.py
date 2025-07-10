import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

async def test_mcp_server(command, args, server_name):
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=None
    )
    
    async with AsyncExitStack() as stack:
        try:
            print(f"\n=== Testing {server_name} ===")
            print(f"Command: {command} {' '.join(args)}")
            print("Connecting to MCP server...")
            
            stdio_transport = await asyncio.wait_for(
                stack.enter_async_context(stdio_client(server_params)),
                timeout=10.0
            )
            stdio, write = stdio_transport
            session = await asyncio.wait_for(
                stack.enter_async_context(ClientSession(stdio, write)),
                timeout=10.0
            )
            await asyncio.wait_for(session.initialize(), timeout=10.0)
            print("✅ Connected successfully!")
            
            # List available tools
            response = await asyncio.wait_for(session.list_tools(), timeout=5.0)
            tools = [tool.name for tool in response.tools]
            print(f"Available tools: {tools}")
            
            # Try to use a simple tool based on server type
            if server_name == "memory" and "store" in tools:
                print("Testing store tool...")
                result = await asyncio.wait_for(
                    session.call_tool("store", {"key": "test", "value": "Hello MCP!"}),
                    timeout=10.0
                )
                print(f"✅ Store result: {result.content}")
                
                print("Testing retrieve tool...")
                result = await asyncio.wait_for(
                    session.call_tool("retrieve", {"key": "test"}),
                    timeout=10.0
                )
                print(f"✅ Retrieve result: {result.content}")
                
            elif server_name == "filesystem" and "list_directory" in tools:
                print("Testing list_directory tool...")
                result = await asyncio.wait_for(
                    session.call_tool("list_directory", {"path": "/tmp"}),
                    timeout=10.0
                )
                print(f"✅ List directory result: {result.content}")
                
            elif server_name == "sqlite" and "execute_query" in tools:
                print("Testing sqlite create table...")
                result = await asyncio.wait_for(
                    session.call_tool("execute_query", {
                        "query": "CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, message TEXT)"
                    }),
                    timeout=10.0
                )
                print(f"✅ Create table result: {result.content}")
                
            elif server_name == "fetch" and "fetch" in tools:
                print("Testing fetch tool with simple URL...")
                result = await asyncio.wait_for(
                    session.call_tool("fetch", {"url": "https://httpbin.org/get"}),
                    timeout=15.0
                )
                print(f"✅ Fetch result: {result.content[:200]}...")
                
            else:
                print(f"⚠️  No specific test for {server_name} with tools {tools}")
                
        except asyncio.TimeoutError:
            print(f"❌ Timeout connecting to {server_name}")
        except Exception as e:
            print(f"❌ Error with {server_name}: {e}")
            import traceback
            traceback.print_exc()

async def main():
    servers_to_test = [
        ("npx", ["-y", "@modelcontextprotocol/server-memory"], "memory"),
        ("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"], "filesystem"),
        ("npx", ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/tmp/test.db"], "sqlite"),
        ("python", ["-m", "mcp_server_fetch"], "fetch"),
    ]
    
    for command, args, name in servers_to_test:
        await test_mcp_server(command, args, name)
        await asyncio.sleep(1)  # Brief pause between tests

if __name__ == "__main__":
    asyncio.run(main()) 