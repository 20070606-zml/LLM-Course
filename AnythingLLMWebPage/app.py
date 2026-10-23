"""本地上传网页：上传文档 -> 加入首个工作区 -> 检查关联结果。"""
from pathlib import Path
from urllib.parse import quote

import uvicorn
from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from AnythingLLMMCP.api import api_client, file_info, first_workspace, request

MAX_SIZE = 20 * 1024 * 1024


async def index(_):
    return FileResponse(Path(__file__).with_name("index.html"))


async def workspace(_):
    try:
        async with api_client() as client:
            return JSONResponse(file_info(await first_workspace(client)))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


async def upload(req):
    # 浏览器只能从本网页发起上传；密钥始终留在 Python 后端。
    origin = req.headers.get("origin")
    if origin and origin != str(req.base_url).rstrip("/"):
        return JSONResponse({"error": "请从本地上传网页提交文件"}, status_code=403)
    try:
        if int(req.headers.get("content-length", "0")) > MAX_SIZE + 1024 * 1024:
            return JSONResponse({"error": "文件不能超过 20 MB"}, status_code=413)
        async with req.form(max_files=1, max_fields=0) as form:
            file = form.get("file")
            if not isinstance(file, UploadFile) or not file.filename:
                return JSONResponse({"error": "请选择一个文件"}, status_code=400)
            content = await file.read(MAX_SIZE + 1)
            if not content or len(content) > MAX_SIZE:
                return JSONResponse({"error": "文件不能为空且不能超过 20 MB"}, status_code=400)
            filename = file.filename.replace("\\", "/").split("/")[-1]
            async with api_client() as client:
                target = await first_workspace(client)
                result = await request(client, "POST", "v1/document/upload",
                                       files={"file": (filename, content, file.content_type or "application/octet-stream")})
                paths = [doc["location"] for doc in result.get("documents", []) if doc.get("location")]
                if not paths:
                    raise ValueError("文档上传后没有返回可嵌入的路径，请检查文档解析服务")
                slug = quote(target["slug"], safe="")
                try:
                    await request(client, "POST", f"v1/workspace/{slug}/update-embeddings",
                                  json={"adds": paths, "deletes": []})
                    current = (await request(client, "GET", f"v1/workspace/{slug}"))["workspace"][0]
                    attached = {doc.get("docpath") for doc in current.get("documents", [])}
                    if not set(paths).issubset(attached):
                        raise ValueError("工作区未包含全部上传文件，请检查嵌入模型和向量库设置")
                except ValueError as exc:
                    raise ValueError("文档已上传，但嵌入未确认完成。" + str(exc)) from None
                return JSONResponse({"message": "上传与工作区嵌入完成", "workspace": target["name"],
                                     "files": paths})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


app = Starlette(routes=[Route("/", index), Route("/workspace", workspace),
                        Route("/upload", upload, methods=["POST"])],
                middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
