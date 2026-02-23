import asyncio
import logging
import sys
import threading
from pathlib import Path
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


class MCPCallError(Exception):
    """Error calling MCP tool or resource."""
    pass
#-------------------------------------------------------------------
class MCPTimeoutError(MCPCallError):
    """MCP call timed out."""
    pass
#-------------------------------------------------------------------
class MCPBridge:
    def __init__(self, server_script: str = "mcp_server.py"): #it runs automatically when you create an object:
        base_dir = Path(__file__).resolve().parents[1]
        self.server_path = (base_dir / server_script).resolve()
        if not self.server_path.exists():
            raise FileNotFoundError(f"Server script not found: {self.server_path}")
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._client = None
        # Use asyncio.Lock for async context safety
        self._client_lock = asyncio.Lock()
        
        # Initialize client immediately
        future = asyncio.run_coroutine_threadsafe(self._ensure_client(), self._loop)
        try:
            future.result(timeout=5)
        except Exception:
            pass  # Client will connect on first use
#-------------------------------------------------------------------
    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
#-------------------------------------------------------------------
    async def _ensure_client(self) -> None:  
        async with self._client_lock:
            if self._client is not None:
                return
            transport = StdioTransport(command=sys.executable, args=["-u", str(self.server_path)])
            self._client = Client(transport)
            await self._client.__aenter__()
#-------------------------------------------------------------------
    def call_tool(self, tool_name: str, args: dict | None = None):
        """Call an MCP tool with comprehensive error handling."""
        if args is None:
            args = {}
        try:
            async def _call():
                await self._ensure_client()
                return await self._client.call_tool(tool_name, args)
            return asyncio.run_coroutine_threadsafe(_call(), self._loop).result(timeout=30)
        except TimeoutError as e:
            raise MCPTimeoutError(f"Tool '{tool_name}' timed out after 30 seconds: {e}")
        except Exception as e:
            raise MCPCallError(f"Failed to call tool '{tool_name}': {e}")
#-------------------------------------------------------------------
    def read_resource(self, uri: str):
        """Read an MCP resource with comprehensive error handling."""
        try:
            async def _call():
                await self._ensure_client()
                return await self._client.read_resource(uri)
            return asyncio.run_coroutine_threadsafe(_call(), self._loop).result(timeout=10)
        except TimeoutError as e:
            raise MCPTimeoutError(f"Resource '{uri}' read timed out after 10 seconds: {e}")
        except Exception as e:
            raise MCPCallError(f"Failed to read resource '{uri}': {e}")
#------------------------------------------------------------------- 
    def list_tools(self):
        """Get list of available tools from MCP server with error handling."""
        try:
            async def _call():
                await self._ensure_client()
                return await self._client.list_tools()
            return asyncio.run_coroutine_threadsafe(_call(), self._loop).result(timeout=10)
        except TimeoutError as e:
            raise MCPTimeoutError(f"Listing tools timed out after 10 seconds: {e}")
        except Exception as e:
            raise MCPCallError(f"Failed to list tools: {e}")
#-------------------------------------------------------------------
    def cleanup(self):
        """Cleanly close the MCP client and stop the event loop."""
        if not self._loop.is_running():
            return

        async def _shutdown():
            if self._client:
                # Close the client session
                await self._client.__aexit__(None, None, None)
            # Stop the loop
            self._loop.stop()

        # Schedule the shutdown coroutine
        try:
            future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
            future.result(timeout=2)  # Wait for cleanup with timeout
        except Exception as e:
            logging.warning(f"MCP cleanup error: {e}")
            
        # Wait for the thread to finish if possible (though it is daemon)
        if self._thread.is_alive():
            self._thread.join(timeout=1)
