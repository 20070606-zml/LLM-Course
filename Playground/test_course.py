"""真实 HTTP 集成测试；上游使用本机模拟服务，不修改任何真实数据库。"""
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import httpx
from mcp import Client

ROOT = Path(__file__).resolve().parents[1]
TEST_KEY = "test-only-not-a-real-key"


class FakeAPI(BaseHTTPRequestHandler):
    state = {}

    def log_message(self, *_):
        pass

    def respond(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        self.state["requests"].append(("GET", url.path))
        if url.path == "/api/v1/pets":
            self.state["query"] = parse_qs(url.query)
            return self.respond({"code": 200, "data": {"items": [{"name": "Demo pet"}], "total": 1}})
        if self.headers.get("Authorization") != "Bearer " + TEST_KEY or self.state["deny"]:
            return self.respond({"error": "unauthorized"}, 403)
        if url.path == "/api/v1/workspaces":
            return self.respond({"workspaces": [] if self.state["empty"] else [
                {"id": 2, "name": "First workspace", "slug": "first"},
                {"id": 1, "name": "Second workspace", "slug": "second"}]})
        if url.path == "/api/v1/workspace/first":
            return self.respond({"workspace": [{"name": "First workspace", "slug": "first",
                                                 "documents": self.state["documents"]}]})
        self.respond({}, 404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.state["requests"].append(("POST", self.path))
        if self.headers.get("Authorization") != "Bearer " + TEST_KEY:
            return self.respond({}, 403)
        if self.path == "/api/v1/document/upload":
            self.state["uploaded"] = body
            return self.respond({"success": not self.state["upload_fail"],
                                 "documents": [{"location": "custom-documents/sample.txt.json"}]})
        if self.path == "/api/v1/workspace/first/update-embeddings":
            self.state["embedding"] = json.loads(body)
            if self.state["embedding_fail"]:
                return self.respond({}, 500)
            if not self.state["skip_attachment"]:
                self.state["documents"] = [{"id": 1, "filename": "sample.txt",
                                             "docpath": path} for path in self.state["embedding"]["adds"]]
            return self.respond({"workspace": {"slug": "first"}})
        self.respond({}, 404)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class CourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix=".test-", dir=ROOT / "Playground")
        cls.addClassCleanup(cls.tmp.cleanup)
        fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeAPI)
        cls.addClassCleanup(fake.server_close)
        cls.addClassCleanup(fake.shutdown)
        threading.Thread(target=fake.serve_forever, daemon=True).start()
        config = Path(cls.tmp.name) / "config.ini"
        config.write_text(f"[pet_hospital]\nbase_url=http://127.0.0.1:{fake.server_port}\n"
                          f"[anythingllm]\nbase_url=http://127.0.0.1:{fake.server_port}/api\napi_key={TEST_KEY}\n")
        env = dict(os.environ, COURSE_CONFIG=str(config), NO_PROXY="127.0.0.1,localhost")
        cls.urls = []
        for module, is_mcp in [("PetHospitalMCP.server", True), ("AnythingLLMMCP.server", True),
                               ("AnythingLLMWebPage.app", False)]:
            port = free_port()
            code = (f"from {module} import mcp; mcp.run(transport='streamable-http',host='127.0.0.1',"
                    f"port={port},stateless_http=True,json_response=True)" if is_mcp else
                    f"from {module} import app; import uvicorn; uvicorn.run(app,host='127.0.0.1',port={port})")
            log = open(Path(cls.tmp.name) / (module + ".log"), "w", encoding="utf-8")
            cls.addClassCleanup(log.close)
            process = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT, env=env, stdout=log,
                                       stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            def stop(p=process):
                if p.poll() is None:
                    p.terminate()
                    p.wait(timeout=10)
            cls.addClassCleanup(stop)
            url = f"http://127.0.0.1:{port}"
            cls.urls.append(url)
            with httpx.Client(trust_env=False, timeout=1) as client:
                for _ in range(80):
                    if process.poll() is not None:
                        raise RuntimeError(f"{module} failed to start; inspect test log")
                    try:
                        client.get(url)
                        break
                    except httpx.RequestError:
                        time.sleep(.1)
                else:
                    raise RuntimeError(f"{module} startup timeout")

    def setUp(self):
        FakeAPI.state = {"requests": [], "documents": [], "empty": False, "deny": False,
                         "upload_fail": False, "embedding_fail": False, "skip_attachment": False}

    async def tool(self, service, name, args=None, mode="2026-07-28"):
        async with Client(self.urls[service] + "/mcp", mode=mode) as client:
            tools = await client.list_tools()
            self.assertEqual([tool.name for tool in tools.tools], [name])
            return await client.call_tool(name, args or {})

    def test_modern_and_legacy_clients(self):
        for mode in ("legacy", "2026-07-28"):
            for index, tool in enumerate(("list_pets", "get_first_workspace_files")):
                with self.subTest(mode=mode, tool=tool):
                    result = asyncio.run(self.tool(index, tool, mode=mode))
                    self.assertFalse(result.is_error)
                    self.assertIsNotNone(result.structured_content)

    def test_filter_sort_pagination_mapping(self):
        args = {"q": "test", "name": "cat", "owner_name": "Demo", "owner_phone": "000",
                "species": "猫", "doctor": "Demo doctor", "disease": "test", "status": "已康复",
                "min_cost": 0, "max_cost": 200, "sort_by": "totalCost", "order": "desc",
                "page": 2, "page_size": 5}
        result = asyncio.run(self.tool(0, "list_pets", args))
        self.assertFalse(result.is_error)
        expected = dict(zip(["q", "name", "ownerName", "ownerPhone", "species", "doctor", "disease",
                             "status", "min", "max", "sortBy", "order", "page", "pageSize"], args.values()))
        for key, value in expected.items():
            actual = FakeAPI.state["query"][key][0]
            self.assertEqual(float(actual), value) if key in ("min", "max") else self.assertEqual(actual, str(value))

    def test_invalid_pagination_and_cost_range(self):
        for args in ({"page": 0}, {"page_size": 101}, {"min_cost": 20, "max_cost": 10}):
            self.assertTrue(asyncio.run(self.tool(0, "list_pets", args)).is_error)
        self.assertEqual(FakeAPI.state["requests"], [])

    def test_modern_direct_post_no_handshake_or_session(self):
        for index, name in enumerate(("list_pets", "get_first_workspace_files")):
            body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
                "name": name, "arguments": {}, "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                    "io.modelcontextprotocol/clientCapabilities": {}}}}
            headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28",
                       "MCP-Method": "tools/call", "MCP-Name": name}
            with httpx.Client(trust_env=False) as client:
                response = client.post(self.urls[index] + "/mcp", json=body, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn("application/json", response.headers["content-type"])
            self.assertNotIn("mcp-session-id", response.headers)
            self.assertFalse(response.json()["result"].get("isError", False))

    def test_older_protocol_versions(self):
        for version in ("2025-03-26", "2025-06-18", "2025-11-25"):
            for index in (0, 1):
                headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": version}
                with httpx.Client(trust_env=False, headers=headers) as client:
                    url = self.urls[index] + "/mcp"
                    response = client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": version, "capabilities": {},
                                   "clientInfo": {"name": "course-test", "version": "1"}}})
                    self.assertEqual(response.json()["result"]["protocolVersion"], version)
                    client.post(url, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
                    response = client.post(url, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                    self.assertEqual(len(response.json()["result"]["tools"]), 1)

    def test_first_workspace_uses_api_order(self):
        FakeAPI.state["documents"] = [{"filename": "sample.txt", "docpath": "custom-documents/sample.txt.json"}]
        result = asyncio.run(self.tool(1, "get_first_workspace_files"))
        self.assertEqual(result.structured_content["workspace"], "First workspace")
        self.assertEqual(result.structured_content["count"], 1)
        self.assertFalse(any("second" in path for _, path in FakeAPI.state["requests"]))

    def test_no_workspace(self):
        FakeAPI.state["empty"] = True
        self.assertTrue(asyncio.run(self.tool(1, "get_first_workspace_files")).is_error)

    def test_bad_api_key_is_not_leaked(self):
        FakeAPI.state["deny"] = True
        result = asyncio.run(self.tool(1, "get_first_workspace_files"))
        self.assertTrue(result.is_error)
        self.assertNotIn(TEST_KEY, str(result))

    def upload(self, content=b"Course sample", **kwargs):
        with httpx.Client(trust_env=False) as client:
            return client.post(self.urls[2] + "/upload", files={"file": ("sample.txt", content, "text/plain")}, **kwargs)

    def test_upload_then_embed(self):
        response = self.upload()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn(b"Course sample", FakeAPI.state["uploaded"])
        self.assertEqual(FakeAPI.state["embedding"], {"adds": ["custom-documents/sample.txt.json"], "deletes": []})
        self.assertEqual([path for method, path in FakeAPI.state["requests"] if method == "POST"],
                         ["/api/v1/document/upload", "/api/v1/workspace/first/update-embeddings"])

    def test_upload_failure_does_not_embed(self):
        FakeAPI.state["upload_fail"] = True
        self.assertEqual(self.upload().status_code, 502)
        self.assertNotIn("embedding", FakeAPI.state)

    def test_embedding_failure_reports_partial_success(self):
        FakeAPI.state["embedding_fail"] = True
        response = self.upload()
        self.assertEqual(response.status_code, 502)
        self.assertIn("已上传", response.json()["error"])

    def test_silent_embedding_failure_is_detected(self):
        FakeAPI.state["skip_attachment"] = True
        self.assertEqual(self.upload().status_code, 502)

    def test_reject_empty_file_and_foreign_origin(self):
        self.assertEqual(self.upload(b"").status_code, 400)
        self.assertEqual(self.upload(headers={"Origin": "https://example.org"}).status_code, 403)
        self.assertEqual(FakeAPI.state["requests"], [])

    def test_page_and_workspace_api(self):
        with httpx.Client(trust_env=False) as client:
            response = client.get(self.urls[2])
            self.assertIn('type="file"', response.text)
            self.assertNotIn(TEST_KEY, response.text)
            self.assertEqual(client.get(self.urls[2] + "/workspace").json()["count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
