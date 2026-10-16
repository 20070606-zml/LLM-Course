"""最简单的命令行 LLM 对话，只使用 Python 标准库。"""

import configparser
import json
import sys
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
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
    settings.getboolean("stream", fallback=True)
    return settings


def ask(settings, messages):
    stream = settings.getboolean("stream", fallback=True)
    payload = {"model": settings["model"].strip(), "messages": messages, "stream": stream}
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
        if stream:
            parts = []
            completed = False
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    completed = True
                    break
                if not data:
                    continue
                chunk = json.loads(data)
                if "error" in chunk:
                    raise ValueError("服务返回流式错误，请检查模型配置或账户状态。")
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                choice = choices[0]
                if choice.get("finish_reason") is not None:
                    completed = True
                text = choice.get("delta", {}).get("content") or ""
                if text:
                    print(text, end="", flush=True)
                    parts.append(text)
            if not completed:
                raise ValueError("流式响应意外中断，本轮回答未保存，请重试。")
            answer = "".join(parts)
            print()
        else:
            answer = json.load(response)["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("模型没有返回文本回答。")
        if not stream:
            print(answer)
        return answer


def main():
    settings = load_config()
    messages = []
    mode = "流式" if settings.getboolean("stream", fallback=True) else "非流式"
    print(f"LLM 对话（{mode}，保留本次运行的聊天记录，Ctrl+C 退出）")
    while True:
        question = input("你：").strip()
        if question:
            print("AI：", end="", flush=True)
            turn = [{"role": "user", "content": question}]
            try:
                answer = ask(settings, messages + turn)
            except HTTPError as exc:
                print(f"\n请求失败（HTTP {exc.code}），请检查密钥、模型名称和账户状态。", file=sys.stderr)
                continue
            except (OSError, HTTPException):
                print("\n网络请求失败，请检查服务地址、网络连接或代理，然后重试。", file=sys.stderr)
                continue
            except ValueError as exc:
                print(f"\n回答处理失败：{exc}", file=sys.stderr)
                continue
            except (KeyError, IndexError, TypeError, AttributeError):
                print("\n模型返回格式不正确，请确认服务支持 Chat Completions 接口。", file=sys.stderr)
                continue
            messages.extend(turn + [{"role": "assistant", "content": answer}])


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n已退出。")
    except ValueError as exc:
        print(f"\n配置错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, configparser.Error):
        print("\n无法读取配置，请检查 config.ini 的内容、编码和文件权限。", file=sys.stderr)
        sys.exit(1)
