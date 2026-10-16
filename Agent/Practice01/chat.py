"""最简单的命令行 LLM 对话，只使用 Python 标准库。"""

import configparser
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_config():
    path = Path(__file__).with_name("config.ini")
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(path, encoding="utf-8-sig"):
        raise ValueError("请把 config.example.ini 复制为 config.ini，填写模型配置。")
    if not config.has_section("llm"):
        raise ValueError("config.ini 缺少 [llm] 配置节。")
    settings = config["llm"]
    for name in ("base_url", "api_key", "model"):
        value = settings.get(name, "").strip()
        if not value or "YOUR_" in value or "your-provider.example" in value:
            raise ValueError(f"请在 config.ini 中填写有效的 {name}。")
    return settings


def ask(settings, messages):
    payload = {"model": settings["model"].strip(), "messages": messages, "stream": False}
    request = Request(
        settings["base_url"].strip().rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + settings["api_key"].strip(),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        answer = json.load(response)["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("模型没有返回文本回答。")
        print(answer)
        return answer


def main():
    settings = load_config()
    question = input("你：").strip()
    if question:
        print("AI：", end="", flush=True)
        ask(settings, [{"role": "user", "content": question}])


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n已退出。")
    except HTTPError as exc:
        print(f"\n请求失败（HTTP {exc.code}），请检查模型配置和账户状态。", file=sys.stderr)
        sys.exit(1)
    except (OSError, URLError, ValueError, KeyError, IndexError, TypeError, configparser.Error):
        print("\n运行失败，请检查 config.ini、网络连接和服务返回格式。", file=sys.stderr)
        sys.exit(1)
