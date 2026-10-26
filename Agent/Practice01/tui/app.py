"""Textual 聊天界面。"""
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static

from core.agent import Agent
from core.tools import ROOT


class Xingya(App):
    TITLE = "星芽 · Xingya"
    SUB_TITLE = "本地 Agent 原型"
    CSS_PATH = "style.tcss"
    BINDINGS = [("ctrl+l", "clear_chat", "清空对话"), ("ctrl+q", "quit", "退出")]

    def __init__(self):
        super().__init__()
        self.agent = Agent()
        self.busy = False
        self.answer = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("✦  星 芽", classes="brand")
                yield Static("本地模型 · 14 个工具", classes="muted")
                yield Static(f"模型\n{self.agent.config['model']}", classes="info")
                yield Static(f"文件范围\n{ROOT}", classes="info")
                yield Static("能力\n日期 · 闰年\n文件 · 目录\n网页 · 搜索", classes="info")
            with Vertical(id="main"):
                yield Static("对话", id="section")
                yield RichLog(id="conversation", markup=False, wrap=True, highlight=False)
                yield Static("就绪 · 输入问题后按 Enter", id="status")
                yield Input(placeholder="问我问题，或让我操作 Playground 文件…", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#conversation", RichLog).write("星芽：你好！我可以查日期、整理 Playground 文件、读取网页和搜索信息。")
        self.query_one("#prompt", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        question = event.value.strip()
        if not question or self.busy:
            return
        event.input.value = ""
        event.input.disabled = True
        self.busy = True
        self.answer = ""
        self.query_one("#conversation", RichLog).write("\n你：" + question)
        self.query_one("#status", Static).update("思考中…")
        self.respond(question)

    def _event(self, kind: str, value: str) -> None:
        if kind == "tool":
            self.query_one("#conversation", RichLog).write("\n↳ 调用工具：" + value)
            self.query_one("#status", Static).update("运行 " + value)
        else:
            self.answer += value
            self.query_one("#status", Static).update("回答中 · " + self.answer[-80:])

    @work(thread=True, exclusive=True)
    def respond(self, question: str) -> None:
        error = None
        try:
            self.agent.ask(question, lambda kind, value: self.call_from_thread(self._event, kind, value))
        except Exception as exc:
            error = str(exc)
        self.call_from_thread(self._finish, error)

    def _finish(self, error: str | None) -> None:
        log = self.query_one("#conversation", RichLog)
        log.write("星芽：" + (self.answer if self.answer else error or "无回答"))
        self.query_one("#status", Static).update("就绪" if not error else "出错 · 可重试")
        self.busy = False
        field = self.query_one("#prompt", Input)
        field.disabled = False
        field.focus()

    def action_clear_chat(self) -> None:
        if not self.busy:
            self.agent.history.clear()
            self.query_one("#conversation", RichLog).clear()
            self.query_one("#status", Static).update("历史已清空")


if __name__ == "__main__":
    Xingya().run()
