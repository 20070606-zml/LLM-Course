# Practice01：最简单的 LLM 多轮对话

一个 `chat.py`，使用 Python 3 标准库发 HTTP 请求，无需 `pip install`。
支持 Chat Completions 兼容接口、普通输出、流式输出、连续输入和聊天历史。

## 1. 填写配置

本机已经生成 `config.ini`；新克隆仓库时先将 `config.example.ini` 复制为 `config.ini`。
在 `config.ini` 中填写你自己的三项配置：

```ini
[llm]
base_url = 服务商给你的接口基础地址
api_key = 你的实际密钥
model = 服务商提供的模型名称
stream = true
```

`base_url` 不包含 `/chat/completions`，程序会自动补上这一段；保留服务商要求的 `/v1` 等路径。
不要使用聊天网页地址。配置文件在脚本旁边，因此从其他目录启动也可以找到它。
配置模板中的占位内容必须替换；未配置时程序会指出缺少哪一项。

## 2. 启动

在 PowerShell 中执行：

```powershell
Set-Location D:\guthub\LLM\Agent\Practice01
.\run.cmd
```

也可以双击 `run.cmd`。启动脚本优先使用本机 Codex 自带的 Python，其他电脑则尝试 `py -3` 或 `python`。
已经安装 Python 的电脑可以直接执行 `python chat.py`。

输入一句话并回车，AI 回复完之后可以继续输入；按 `Ctrl+C` 退出。
空白输入不会调用模型。关闭程序后聊天历史消失，再次启动会开启新对话。

配置错误时，双击启动的窗口可能立即关闭；在 PowerShell 中运行可以保留错误提示。

## 3. 对比两种输出

把 `config.ini` 中的 `stream` 设为 `false` 后重新启动，回答会在完整返回后一次显示。
设为 `true` 后重新启动，回答会随服务返回的文本分片立即显示，不添加人为延迟。

## 4. 验证上下文

依次输入：

```text
我叫小明，请记住我的名字。
我叫什么名字？
```

第二次请求会携带第一次的用户输入、AI 回答和当前问题。
历史保存在内存里的 `messages` 列表；只有成功完成的问答才加入，失败请求不会污染后续历史。
程序按课程要求发送全部历史；对话很长时仍会受到服务商上下文长度限制，此时可退出并重新启动。

## 5. 本地测试

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 -m unittest discover -s . -p test_chat.py -v
```

其他已经安装 Python 的电脑可以执行 `python -m unittest discover -s . -p test_chat.py -v`。
测试只连接 `127.0.0.1` 上的模拟 HTTP 服务，使用虚构测试密钥，不消耗真实模型额度。
测试覆盖普通输出、真正的流式实时输出、聊天历史、空输入、配置缺失、失败后重试和流意外中断。
这套测试证明客户端逻辑可运行；真实模型连通性需要填写实际服务配置后单独验证。

## 6. 查看课程每一步

在仓库根目录执行 `git log --oneline --reverse`，可以依次看到：

1. `week4 step1`：单次普通输出与配置文件。
2. `week4 step2`：流式输出，保留 `stream = false` 的对照模式。
3. `week4 step3`：仅用 `while True` 包住输入和请求，没有添加其他逻辑。
4. `week4 step4`：每次请求发送此前全部成功的聊天记录。
5. 后续收尾提交：错误处理、启动脚本、提示词与验收材料。

使用 `git show 提交编号:Agent/Practice01/chat.py` 查看对应阶段，不必覆盖当前文件。
分阶段开发使用的自然语言要求保存在 [PROMPTS.md](PROMPTS.md)。

## 接口参考

实现依据 OpenAI 官方的 [Chat Completions 请求格式](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
和 [流式事件格式](https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events)。
其他服务需要兼容同样的请求结构及流式事件格式。
