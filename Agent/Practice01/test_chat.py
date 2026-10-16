"""用本地 HTTP 服务验收；不连接真实模型，不需要真实密钥。"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.received.append((self.path, self.headers.get("Authorization"), body))
        question = body["messages"][-1]["content"]
        if question == "HTTP错误":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"invalid test credential"}}')
            return
        if question == "我叫什么？":
            answer = "你叫小明。" if any(
                item["content"] == "我叫小明。" for item in body["messages"][:-1]
            ) else "没有收到之前的名字。"
        else:
            answer = "你好，已收到。"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream" if body["stream"] else "application/json")
        self.end_headers()
        if not body["stream"]:
            self.wfile.write(json.dumps({"choices": [{"message": {"content": answer}}]}).encode())
            return
        self.wfile.write(b': keep-alive\n\ndata: {"choices":[]}\n\n')
        for index, text in enumerate((answer[:3], answer[3:])):
            chunk = {"choices": [{"delta": {"content": text}, "finish_reason": None}]}
            self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n").encode())
            self.wfile.flush()
            if question == "验证实时输出" and index == 0:
                self.server.first_chunk.set()
                self.server.release_chunk.wait(timeout=8)
        if question != "截断流":
            self.wfile.write(b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n')
            self.wfile.write(b"data: [DONE]\n\n")


class ChatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.server.first_chunk = threading.Event()
        cls.server.release_chunk = threading.Event()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.server.received = []
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".test-chat-", dir=Path(__file__).resolve().parent,
        )
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        shutil.copyfile(Path(__file__).with_name("chat.py"), self.directory / "chat.py")

    def configure(self, stream=True):
        config = (
            "[llm]\n"
            f"base_url = http://127.0.0.1:{self.server.server_port}/v1/\n"
            "api_key = local-test-key-with-%-character\nmodel = local-test-model\n"
            f"stream = {str(stream).lower()}\n"
        )
        (self.directory / "config.ini").write_text(config, encoding="utf-8-sig")

    def command(self):
        return [sys.executable, "-X", "utf8", str(self.directory / "chat.py")]

    def run_chat(self, text):
        return subprocess.run(
            self.command(), input=text, capture_output=True, encoding="utf-8",
            cwd=self.directory.parent, timeout=12,
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    def test_non_streaming(self):
        self.configure(False)
        result = self.run_chat("你好\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("你好，已收到。", result.stdout)
        path, authorization, body = self.server.received[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(authorization, "Bearer local-test-key-with-%-character")
        self.assertFalse(body["stream"])

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_windows_launcher(self):
        self.configure(False)
        launcher = self.directory / "run.cmd"
        shutil.copyfile(Path(__file__).with_name("run.cmd"), launcher)
        result = subprocess.run(
            [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(launcher)],
            input="你好\n", capture_output=True, encoding="utf-8", timeout=12,
            cwd=self.directory.parent,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("你好，已收到。", result.stdout)

    def test_streaming(self):
        self.configure()
        result = self.run_chat("你好\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("你好，已收到。", result.stdout)
        self.assertTrue(self.server.received[0][2]["stream"])

    def test_history_in_both_modes(self):
        for stream in (False, True):
            with self.subTest(stream=stream):
                self.server.received = []
                self.configure(stream)
                result = self.run_chat("我叫小明。\n我叫什么？\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("你叫小明。", result.stdout)
                messages = self.server.received[1][2]["messages"]
                self.assertEqual([m["role"] for m in messages], ["user", "assistant", "user"])
                self.assertEqual(messages[1]["content"], "你好，已收到。")

    def test_blank_input_makes_no_request(self):
        self.configure()
        result = self.run_chat("  \n\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.server.received, [])

    def test_missing_config(self):
        result = self.run_chat("")
        self.assertEqual(result.returncode, 1)
        self.assertIn("config", result.stderr)
        self.assertEqual(self.server.received, [])

    def test_placeholder_config(self):
        shutil.copyfile(Path(__file__).with_name("config.example.ini"), self.directory / "config.ini")
        result = self.run_chat("")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.server.received, [])

    def test_invalid_stream_setting(self):
        self.configure()
        path = self.directory / "config.ini"
        path.write_text(path.read_text(encoding="utf-8-sig").replace("stream = true", "stream = invalid"), encoding="utf-8")
        result = self.run_chat("")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.server.received, [])

    def test_ctrl_c_exits_without_traceback(self):
        self.configure()
        script = (
            "import runpy, sys\nfrom unittest.mock import patch\n"
            "with patch('builtins.input', side_effect=KeyboardInterrupt):\n"
            "    runpy.run_path(sys.argv[1], run_name='__main__')\n"
        )
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-c", script, str(self.directory / "chat.py")],
            capture_output=True, encoding="utf-8", timeout=12,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("已退出", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_http_failure_does_not_poison_history(self):
        self.configure()
        result = self.run_chat("我叫小明。\nHTTP错误\n我叫什么？\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("401", result.stderr)
        self.assertNotIn("local-test-key", result.stderr)
        messages = self.server.received[-1][2]["messages"]
        self.assertEqual([m["content"] for m in messages], ["我叫小明。", "你好，已收到。", "我叫什么？"])

    def test_truncated_stream_is_not_saved(self):
        self.configure()
        result = self.run_chat("截断流\n你好\n")
        self.assertIn("中断", result.stderr)
        self.assertEqual(self.server.received[-1][2]["messages"], [{"role": "user", "content": "你好"}])

    def test_output_arrives_before_stream_finishes(self):
        self.configure()
        self.server.first_chunk.clear()
        self.server.release_chunk.clear()
        process = subprocess.Popen(
            self.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"},
        )
        output_received = threading.Event()
        prefix = []

        def read_prefix():
            while True:
                char = process.stdout.read(1)
                if not char:
                    return
                prefix.append(char)
                if "你好，" in "".join(prefix):
                    output_received.set()
                    return

        reader = threading.Thread(target=read_prefix, daemon=True)
        reader.start()
        try:
            process.stdin.write("验证实时输出\n")
            process.stdin.flush()
            self.assertTrue(self.server.first_chunk.wait(4), "服务未发出第一个分片")
            self.assertTrue(output_received.wait(3), "回复在结束前未实时显示")
        finally:
            self.server.release_chunk.set()
            process.stdin.close()
            process.wait(timeout=10)
            reader.join(timeout=2)
            process.stdout.close()
            process.stderr.close()
        self.assertEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
