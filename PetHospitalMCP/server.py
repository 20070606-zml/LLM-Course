"""Only one tool: GET /api/v1/pets."""
import configparser
import os
from pathlib import Path
from typing import Annotated, Literal

import httpx
from mcp.server import MCPServer
from pydantic import Field

mcp = MCPServer("PetHospitalMCP")


@mcp.tool()
async def list_pets(
    q: str = "", name: str = "", owner_name: str = "", owner_phone: str = "",
    species: str = "", doctor: str = "", disease: str = "", status: str = "",
    min_cost: Annotated[float | None, Field(ge=0)] = None,
    max_cost: Annotated[float | None, Field(ge=0)] = None,
    sort_by: Literal["id", "name", "ownerName", "species", "doctor", "disease",
                     "status", "totalCost", "visitCount", "createdAt", "updatedAt"] = "id",
    order: Literal["asc", "desc"] = "asc",
    page: Annotated[int, Field(ge=1)] = 1,
    page_size: Annotated[int, Field(ge=1, le=100)] = 20,
) -> dict[str, object]:
    """查询宠物列表。q 搜索；min/max_cost 按总费用过滤；支持排序、分页。"""
    if min_cost is not None and max_cost is not None and min_cost > max_cost:
        raise ValueError("min_cost 不能大于 max_cost")
    config = configparser.ConfigParser(interpolation=None)
    config.read(os.environ.get("COURSE_CONFIG", Path(__file__).resolve().parents[1] / "config.ini"), encoding="utf-8-sig")
    base = config.get("pet_hospital", "base_url", fallback="http://127.0.0.1:8080").rstrip("/")
    params = {"q": q, "name": name, "ownerName": owner_name, "ownerPhone": owner_phone,
              "species": species, "doctor": doctor, "disease": disease, "status": status,
              "min": min_cost, "max": max_cost, "sortBy": sort_by, "order": order,
              "page": page, "pageSize": page_size}
    params = {key: value for key, value in params.items() if value is not None and value != ""}
    try:
        async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
            response = await client.get(base + "/api/v1/pets", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"宠物医院接口返回 HTTP {exc.response.status_code}") from None
    except httpx.RequestError:
        raise ValueError("无法连接宠物医院服务，请先启动 pethospital.exe") from None


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000,
            stateless_http=True, json_response=True)
