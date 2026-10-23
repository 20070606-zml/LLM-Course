"""MCP 与上传网页共用的少量 AnythingLLM API 调用。"""
import configparser
import os
from pathlib import Path
from urllib.parse import quote

import httpx


def api_client() -> httpx.AsyncClient:
    config = configparser.ConfigParser(interpolation=None)
    config.read(os.environ.get("COURSE_CONFIG", Path(__file__).resolve().parents[1] / "config.ini"), encoding="utf-8-sig")
    key = config.get("anythingllm", "api_key", fallback="").strip()
    if not key:
        raise ValueError("请在课程根目录的 config.ini 中填写 AnythingLLM api_key")
    base = config.get("anythingllm", "base_url", fallback="http://127.0.0.1:3001/api")
    return httpx.AsyncClient(base_url=base.rstrip("/") + "/", timeout=120,
                             headers={"Authorization": "Bearer " + key}, trust_env=False)


async def request(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> dict:
    try:
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"AnythingLLM 返回 HTTP {exc.response.status_code}；请检查服务及 API Key") from None
    except httpx.RequestError:
        raise ValueError("AnythingLLM 无法连接或请求超时，请检查服务") from None
    except ValueError:
        raise ValueError("AnythingLLM 未返回有效 JSON") from None
    if data.get("success") is False or data.get("error"):
        raise ValueError("AnythingLLM 未完成操作，请在其界面查看文档处理或嵌入设置")
    return data


async def first_workspace(client: httpx.AsyncClient) -> dict:
    workspaces = (await request(client, "GET", "v1/workspaces")).get("workspaces", [])
    if not workspaces:
        raise ValueError("没有工作区，请先在 AnythingLLM 中创建一个工作区")
    slug = quote(workspaces[0]["slug"], safe="")
    items = (await request(client, "GET", f"v1/workspace/{slug}")).get("workspace", [])
    if not items:
        raise ValueError("第一个工作区已不存在，请刷新后重试")
    return items[0]


def file_info(workspace: dict) -> dict:
    fields = ("id", "filename", "docpath", "createdAt", "lastUpdatedAt")
    documents = [{key: doc[key] for key in fields if key in doc}
                 for doc in workspace.get("documents", [])]
    return {"workspace": workspace["name"], "slug": workspace["slug"],
            "count": len(documents), "documents": documents}
