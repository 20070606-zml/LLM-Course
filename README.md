# LLM 课程实践

三个 MVP：宠物列表 MCP、AnythingLLM 首个工作区文件信息 MCP、文档上传及嵌入网页。

## 目录

```text
D:\LLM-Course
├─PetHospitalServer     老师提供的服务器、说明及本地数据
├─PetHospitalMCP        仅 list_pets
├─AnythingLLMMCP        仅 get_first_workspace_files
├─AnythingLLMWebPage    上传、工作区嵌入和结果检查
├─Playground           MCP 配置、测试和测试文档
└─Agent\Practice01     保留的第四周作业
```

本次从原课程目录复制整理，原目录保留。后续开发请使用本目录，避免两份副本混用。

## 运行

本机已准备 `.venv`。在各项目中双击 `run.cmd` 即可启动对应程序，Ctrl+C 退出。
也可以在三个 PowerShell 窗口分别执行：

```powershell
cd D:\LLM-Course
.\.venv\Scripts\python.exe -m PetHospitalMCP.server
# 另一个窗口
.\.venv\Scripts\python.exe -m AnythingLLMMCP.server
# 第三个窗口
.\.venv\Scripts\python.exe -m AnythingLLMWebPage.app
```

先运行 `PetHospitalServer\pethospital.exe`，默认 REST 地址为 http://127.0.0.1:8080 。
若已有实例运行，不要重复启动。

| 程序 | 地址 |
|---|---|
| 宠物医院 MCP | http://127.0.0.1:8000/mcp |
| AnythingLLM MCP | http://127.0.0.1:8001/mcp |
| 上传网页 | http://127.0.0.1:8002 |

MCP 地址供 MCP 客户端连接，不能当作普通网页打开测试。

另一台电脑需 Python 3.11+，在课程根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.ini config.ini
```

## AnythingLLM 配置

启动 AnythingLLM，创建至少一个工作区、设置好嵌入模型与向量库，并在其设置中创建 API Key。
本地文档入口：http://localhost:3001/api/docs/ 。
只在根目录 `config.ini` 的 `[anythingllm]` 中填写 `api_key`，按实际服务修改 `base_url`（默认含 `/api`）。
两个程序共用此配置；密钥由 Python 后端读取，不放进 HTML 或 MCP 客户端配置。

“第一个工作区”指 `GET /v1/workspaces` 返回列表的第一项，界面显示其名称。
MCP 返回该工作区的文件名称、文档路径和时间等信息，不进行模型问答或正文内容提取。
网页依次调用 `POST /v1/document/upload`、`POST /v1/workspace/{slug}/update-embeddings`，再查询工作区核对文档关联。
嵌入失败时会提示上传已完成，避免误报全部成功；可在 AnythingLLM 中处理已上传文档。

## MCP 配置与测试

`Playground/mcp.json` 是通用地址配置示例；不同客户端的配置键可能不同。
OpenCode 使用 `Playground/opencode.json`。先启动两个 MCP，然后在 Playground 中运行 OpenCode。
示例提示词：“使用 pet-hospital 查询猫，按总费用降序，第一页五条。”
示例提示词：“使用 anythingllm 提取第一个工作区的文件信息。”

两个 MCP 使用官方 SDK 2.3.0 的 Streamable HTTP，开启无状态 HTTP 和 JSON 响应。
旧客户端仍按旧协议握手；2026-07-28 客户端可直接调用，无需初始化握手或长连接。
已验证版本：2025-03-26、2025-06-18、2025-11-25、2026-07-28；不承诺尚未发布的未来协议。

```powershell
cd D:\LLM-Course
.\.venv\Scripts\python.exe -m unittest Playground.test_course -v
```

测试使用隔离的模拟上游，不修改真实宠物或工作区数据。范围见 `Playground/TEST_REPORT.md`。

## 提交与隐私

只提交源代码、说明、空密钥模板和测试材料。`config.ini`、数据库、exe、虚拟环境和日志已忽略。
Git 忽略规则无法撤回历史已提交内容；上传前仍需检查暂存文件及历史。
老师的 exe 在本机保留；从 GitHub 获取代码的同学应自行下载发行包。
本次新增的三个项目尚未推送到 GitHub。第四周原有提交历史保留。

## 参考

- [老师的宠物医院项目](https://github.com/atfa/pet-hospital-mcp-teaching)
- [服务器发行包](https://github.com/atfa/pet-hospital-mcp-teaching/releases/tag/v1.0.0)
- [MCP 官方 SDK 新旧客户端说明](https://py.sdk.modelcontextprotocol.io/run/legacy-clients/)
- [AnythingLLM API](https://docs.anythingllm.com/features/api)
- [OpenCode MCP 配置](https://opencode.ai/docs/mcp-servers/)
