# 星芽 Agent 原型

这是第四周单文件聊天程序的后续原型。`chat.py` 保留原作业；新功能在 `core` 和 `tui` 中。

启动：双击 `run-agent.cmd`。脚本先启动 D 盘 Ollama，再打开 Textual 界面。
输入问题后按 Enter。`Ctrl+L` 清空当前对话，`Ctrl+Q` 退出。

本地模型配置仍读同目录被 Git 忽略的 `config.ini`，当前使用 `http://127.0.0.1:11434/v1`、`qwen3:4b`。
新电脑安装依赖：在课程根目录执行 `.\.venv\Scripts\python.exe -m pip install -r Agent\Practice01\requirements-agent.txt`。

12 个函数：

1. `get_local_date`：通过 `subprocess` 执行 Windows `date /t`。
2. `is_current_year_leap`：Python 内部算法判断当前年份。
3. `get_current_directory`：返回可操作目录。
4. `list_directory`：列出文件和目录。
5. `get_file_type`：查看文件类型。
6. `read_text_file`：读取 UTF-8 纯文本。
7. `modify_text_file`：替换一次精确匹配的文字。
8. `create_text_file`：在目录中创建文本文件。
9. `create_directory`：创建目录。
10. `rename_item`：重命名文件或目录。
11. `delete_directory`：删除非空目录。
12. `delete_file`：删除文件。

文件工具仅可操作 `D:\LLM-Course\Playground` 及其子目录；路径越界会拒绝。文本限制 100 KB，列表最多显示 100 项。请先在 Playground 建立练习目录，再让 Agent 操作。
模型自行选择工具；可能选错。删除命令会立即执行，仅在练习目录使用。

测试：12 个函数的实际调用、路径越界拦截、Textual 组件挂载、真实 Ollama 闰年 function call 均通过。测试记录见 `TEST_AGENT.md`。
架构图在 `ARCHITECTURE.md`。
