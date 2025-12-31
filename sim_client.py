import asyncio
import httpx
import json
import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def send_mcp_request(client, server_url, request_data, session_id=None):
    """
    Send an MCP request and parse SSE response.
    The server uses Server-Sent Events to stream responses.
    """
    response_data = None
    
    try:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        }
        
        # Add session ID if provided
        if session_id:
            headers["mcp-session-id"] = session_id
        
        # Use streaming to handle SSE responses
        async with client.stream(
            "POST",
            server_url,
            json=request_data,
            headers=headers
        ) as response:
            if response.status_code != 200:
                content = await response.aread()
                error_text = content.decode('utf-8')
                print(f"Error: {response.status_code}")
                print(f"Response: {error_text}")
                return None, None
            
            # Parse SSE format responses
            async for line in response.aiter_lines():
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith(':'):
                    continue
                
                # Check for data lines
                if line.startswith('data:'):
                    data_str = line[5:].strip()  # Remove 'data:' prefix
                    try:
                        response_data = json.loads(data_str)
                    except json.JSONDecodeError:
                        pass
            
            # Extract session ID from headers if present
            new_session_id = response.headers.get('mcp-session-id') or response.headers.get('x-session-id')
            
    except Exception as e:
        print(f"Error in request: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    return response_data, new_session_id

async def main():
    """
    HTTP MCP client using httpx to connect to the greeting server.
    The server uses SSE (Server-Sent Events) for bi-directional communication.
    """
    # Server URL
    server_url = "http://127.0.0.1:8000/mcp"
    
    print(f"Connecting to MCP server at {server_url}...\n")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Initialize the MCP connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0"
                    }
                }
            }
            
            print("Initializing connection...\n")
            
            init_response, session_id = await send_mcp_request(client, server_url, init_request)
            
            if not init_response:
                print("Failed to initialize server connection")
                return
            
            print("[OK] Connected to MCP server\n")
            server_info = init_response.get('result', {}).get('serverInfo', {})
            print(f"Server name: {server_info.get('name', 'unknown')}")
            print(f"Server version: {server_info.get('version', 'unknown')}\n")
            print(f"Session ID: {session_id}\n")
            
            # List available tools - use the session ID
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            print("Fetching available tools...\n")
            tools_response, _ = await send_mcp_request(client, server_url, list_request, session_id)
            
            if tools_response and 'result' in tools_response:
                tools = tools_response.get('result', {}).get('tools', [])
                print("Available tools:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'N/A')}")
                
                print()
                
                # Call the greet tool with different names
                names = ["tea", "stu"]
                
                for idx, name in enumerate(names):
                    call_request = {
                        "jsonrpc": "2.0",
                        "id": 3 + idx,
                        "method": "tools/call",
                        "params": {
                            "name": "greet",
                            "arguments": {"name": name}
                        }
                    }
                    
                    result, _ = await send_mcp_request(client, server_url, call_request, session_id)
                    
                    if result and 'result' in result:
                        content = result.get('result', {}).get('content', [])
                        print(f"Greeting for {name}:")
                        
                        if content and len(content) > 0:
                            text = content[0].get('text', 'No response')
                            print(f"  {text}")
                        else:
                            print(f"  (No response)")
                        print()
                    else:
                        print(f"Error calling tool for {name}")
                        if result:
                            print(f"Response: {result}")
            else:
                print(f"Error listing tools")
                if tools_response:
                    print(f"Response: {tools_response}")
                
    except httpx.ConnectError as e:
        print("[ERROR] Could not connect to server")
        print(f"Error: {e}")
        print("\nMake sure the server is running:")
        print("  python sim_server.py")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Verify server is running: python sim_server.py")
        print("2. Check server URL is correct: http://127.0.0.1:8000/mcp")
        print("3. Check server logs for any errors")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nClient stopped.")
