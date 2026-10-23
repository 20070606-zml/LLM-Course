"""Only one read-only MCP tool."""
from mcp.server import MCPServer
from AnythingLLMMCP.api import api_client, file_info, first_workspace

mcp = MCPServer("AnythingLLMMCP")


@mcp.tool()
async def get_first_workspace_files() -> dict[str, object]:
    """提取第一个工作区已关联文件的名称、路径和时间信息。"""
    async with api_client() as client:
        return file_info(await first_workspace(client))


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001,
            stateless_http=True, json_response=True)
