from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("Greeting Server")

@mcp.tool()
def greet(name: str) -> str:
    """
    A simple greeting tool that says hello to someone.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        A friendly greeting message
    """
    return f"Hello, {name}! Welcome to the FastMCP server!"

# Run with HTTP streaming support
if __name__ == "__main__":
    # Start server with streamable HTTP transport
    mcp.run(transport="streamable-http")
