"""对话、流式输出、工具调用与聊天历史。"""
import configparser
import json
from pathlib import Path
from urllib.request import Request, urlopen

from .tools import call, specs


def load_skills() -> str:
    """每轮对话重新读取项目中的 SKILL.md。"""
    root = Path(__file__).resolve().parents[1] / ".agents" / "skills"
    found = []
    for path in sorted(root.glob("*/SKILL.md")):
        if path.is_file() and path.stat().st_size <= 8000:
            found.append(path.read_text(encoding="utf-8-sig"))
    return "\n\n".join(found[:10])


def settings() -> dict:
    config = configparser.ConfigParser(interpolation=None)
    path = Path(__file__).resolve().parents[1] / "config.ini"
    if not config.read(path, encoding="utf-8-sig"):
        raise ValueError("缺少 config.ini")
    result = dict(config["llm"])
    for field in ("base_url", "api_key", "model"):
        if not result.get(field) or "YOUR_" in result[field] or "your-provider.example" in result[field]:
            raise ValueError("请先配置 " + field)
    return result


class Agent:
    def __init__(self):
        self.config = settings()
        self.history: list[dict] = []

    def _completion(self, messages: list[dict], emit):
        payload = {"model": self.config["model"], "messages": messages,
                   "stream": True, "tools": specs(), "tool_choice": "auto"}
        request = Request(self.config["base_url"].rstrip("/") + "/chat/completions",
                          data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                          headers={"Authorization": "Bearer " + self.config["api_key"],
                                   "Content-Type": "application/json"}, method="POST")
        parts, calls, done = [], {}, False
        with urlopen(request, timeout=120) as response:
            for raw in response:
                if not raw.startswith(b"data:"):
                    continue
                data = raw[5:].strip()
                if data == b"[DONE]":
                    done = True
                    break
                if not data:
                    continue
                chunk = json.loads(data)
                if chunk.get("error"):
                    raise ValueError("模型返回错误")
                for choice in chunk.get("choices", []):
                    if choice.get("finish_reason") is not None:
                        done = True
                    delta = choice.get("delta") or {}
                    text = delta.get("content") or ""
                    if text:
                        parts.append(text)
                        emit("text", text)
                    for tool in delta.get("tool_calls", []):
                        index = tool["index"]
                        item = calls.setdefault(index, {"id": "", "type": "function",
                                                         "function": {"name": "", "arguments": ""}})
                        item["id"] += tool.get("id") or ""
                        function = tool.get("function") or {}
                        item["function"]["name"] += function.get("name") or ""
                        item["function"]["arguments"] += function.get("arguments") or ""
        if not done:
            raise ValueError("模型响应中断")
        return "".join(parts), [calls[index] for index in sorted(calls)]

    def ask(self, question: str, emit) -> str:
        skill_text = load_skills()
        system = [{"role": "system", "content": "按需遵循以下本地 Skills：\n" + skill_text}] if skill_text else []
        messages = system + self.history + [{"role": "user", "content": question}]
        for _ in range(6):
            answer, tool_calls = self._completion(messages, emit)
            if not tool_calls:
                if not answer.strip():
                    raise ValueError("模型没有返回文本")
                self.history = messages[len(system):] + [{"role": "assistant", "content": answer}]
                return answer
            messages.append({"role": "assistant", "content": answer or None, "tool_calls": tool_calls})
            for tool in tool_calls:
                name = tool["function"]["name"]
                emit("tool", name)
                result = call(name, tool["function"]["arguments"])
                messages.append({"role": "tool", "tool_call_id": tool["id"], "content": result})
        raise ValueError("工具调用次数过多，已停止")
