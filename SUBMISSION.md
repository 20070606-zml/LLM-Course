# 第四周作业提交说明

本项目使用 Codex 在本机实际开发，核心程序为 `Agent/Practice01/chat.py`，无需安装第三方 Python 包。

## 老师要求逐项对照

| 课程步骤 | 实际成果或证据 | 完成情况 |
| --- | --- | --- |
| 1. 理解单次对话与 INI 配置需求 | `chat.py`、`config.example.ini`；实际 `config.ini` 只在本机保存 | 已完成 |
| 2. 先用自然语言获得简单开发提示词 | `Agent/Practice01/PROMPTS.md` 的阶段一 | 已完成 |
| 3. 在 Agent/Practice01 开发 | 目录和代码已建立，使用 Codex 执行提示词意图；没有使用 opencode | 开发已完成，工具与原课程示例不同 |
| 4. 验证非流式输出 | `week4 step1` 提交及 `test_non_streaming` | 模拟接口通过 |
| 5. 获得打字机输出改造提示词 | `PROMPTS.md` 的阶段二 | 已完成 |
| 6. 根据提示词改造程序 | `week4 step2` 提交 | 已完成 |
| 7. 验证 Stream 输出 | `test_streaming` 和 `test_output_arrives_before_stream_finishes` | 模拟接口通过 |
| 8. 仅添加无限循环，Ctrl+C 退出 | `week4 step3` 对 chat.py 只添加循环并缩进原有问答代码；后续验证退出处理 | 已完成 |
| 9. 每轮发送此前全部聊天记录 | `week4 step4` 和 `test_history_in_both_modes` | 已完成 |
| 10. 根目录 .gitignore 添加 config.ini | 忽略规则已生效；实际配置从未进入提交历史 | 已完成 |
| 11. 上传 GitHub | 新建公开仓库 `20070606-zml/LLM-Course`，保留全部分阶段提交，不覆盖其他仓库 | 已完成，使用 Git 命令推送，未使用 VSCode 界面 |

## 如何查看 AI 开发过程

1. 阅读 `PROMPTS.md`，观察需求如何从单次对话逐步增加流式、循环和历史。
2. 在仓库根目录运行 `git log --oneline --reverse`，查看分阶段实际提交。
3. 使用 `git show 提交编号:Agent/Practice01/chat.py` 查看当时的代码。
4. 使用 `git show 71ec19c -- Agent/Practice01/chat.py` 检查第三阶段仅添加循环的改动。
5. 运行测试，或阅读 `TEST_RESULTS.txt` 与 `TEST_REPORT.md` 核对证据。

这些提示词是本次开发阶段的整理记录，不是 opencode 的执行日志。程序、测试和 Git 提交均在本机实际生成。

## 运行方法

在仓库根目录进入 `Agent/Practice01`，复制 `config.example.ini` 为 `config.ini`，仅在本机填写服务地址、模型名称及密钥。
运行 `run.cmd`；普通输出设置 `stream = false`，流式输出设置 `stream = true`，修改后重新启动程序。
输入后按回车，连续对话时保留此前所有成功问答；按 `Ctrl+C` 退出。

未配置真实模型时，不能直接获得真实 AI 回答。可以运行 `test_chat.py` 进行无需真实密钥的本地模拟验收，详细命令见项目 README。

## 测试与隐私边界

现有 12 项测试通过本机模拟 HTTP 服务验证客户端行为，没有消耗真实模型额度。实时流式测试会暂停服务的后续分片，确认首个分片已经显示。
Ctrl+C 测试通过模拟 `KeyboardInterrupt` 验证退出路径。
没有声称完成真实服务调用，也没有虚构前三周代码。

公开内容限于代码、说明、提示词、测试、测试结果和脱敏模板。真实配置、密钥、令牌、私人邮箱和含用户名的本机路径不进入公开仓库。
提交前检查当前跟踪文件、Git 可达历史及提交者信息，并核实忽略规则生效。

## 发布记录

公开地址：[20070606-zml/LLM-Course](https://github.com/20070606-zml/LLM-Course)。

发布时间：2026-10-16（Asia/Shanghai）。已创建公开仓库并将全部阶段提交推送到 `main`，没有覆盖已有仓库，也没有改写开发历史。

通过不带凭据的 GitHub 公开接口核对了仓库可见性、默认分支、文件列表、提交数量及远端与本地提交的一致性。
公开文件中没有实际 `config.ini`；模型密钥和 GitHub 登录凭据均未进入仓库。


## 2026-10-23：前三次 MVP 任务补充

目录已整理至 D:\LLM-Course，第四周代码保留。新增宠物医院单工具 MCP、AnythingLLM 文件信息单工具 MCP、上传嵌入网页及 Playground 配置。14 项模拟上游 HTTP 集成测试通过，宠物医院另用真实 exe 验证。AnythingLLM 未配置密钥、未启动，真实向量化待验收。本次新增内容仅在本地，尚未推送。详见根目录 README.md 与 Playground/TEST_REPORT.md。
