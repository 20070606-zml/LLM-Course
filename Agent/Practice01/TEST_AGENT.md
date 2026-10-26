# 星芽原型测试

2026-10-24，本机 Python 3.12 / Textual 6.12.0 / Ollama 0.40.8 / qwen3:4b。

- 12 个工具均运行；在 Playground 临时目录实测创建、读取、修改、重命名、删除文件和目录。
- `../Agent/Practice01/config.ini` 路径越界读取被拒绝。
- Textual 的主界面、对话日志、输入框和侧栏在 100×32 终端模拟环境成功挂载。
- 真正调用本地 Qwen3 4B：提问当前年份是否为闰年，模型调用 `is_current_year_leap`，回答非空；历史依次含 user、assistant tool_calls、tool、assistant。
- 原始第四周 `chat.py` 保留，没有参与新的工具派发。

架构图采用 Mermaid 基本流程图语法；源文件可导入 mermaid.live。尚未在该网站做交互式校验。
- 2026-10-26：模拟 TUI 输入、回复和 Ctrl+L 清空历史，通过。
