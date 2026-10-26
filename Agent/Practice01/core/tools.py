"""12 个教学用函数。文件操作只允许在 Playground 内。"""
import json
import mimetypes
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "Playground"
MAX_TEXT = 100_000


def _path(value: str, *, create: bool = False) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path != ROOT and ROOT not in path.parents:
        raise ValueError("路径必须位于 Playground 内")
    if any(part.startswith(".test-") for part in path.parts):
        raise ValueError("测试目录不能修改")
    if create and path == ROOT:
        raise ValueError("不能修改 Playground 根目录")
    return path


def _text(content: str) -> str:
    if len(content.encode("utf-8")) > MAX_TEXT:
        raise ValueError("文本不能超过 100 KB")
    return content


def _read(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > MAX_TEXT:
        raise ValueError("仅能读取不超过 100 KB 的纯文本文件")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeError:
        raise ValueError("文件不是 UTF-8 纯文本") from None
    if "\x00" in content:
        raise ValueError("文件包含二进制内容")
    return content


def get_local_date() -> str:
    """通过 Windows 本地 date 命令获取日期。"""
    result = subprocess.run(["cmd", "/c", "date", "/t"], capture_output=True,
                            text=True, check=True, timeout=5)
    return result.stdout.strip()


def is_current_year_leap() -> dict:
    year = datetime.now().year
    return {"year": year, "is_leap": year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)}


def get_current_directory() -> str:
    return str(ROOT)


def list_directory(directory: str = ".") -> list[dict]:
    path = _path(directory)
    if not path.is_dir():
        raise ValueError("目录不存在")
    return [{"name": item.name, "type": "directory" if item.is_dir() else "file"}
            for item in sorted(path.iterdir(), key=lambda p: p.name.lower()) if not item.name.startswith(".test-")][:100]


def get_file_type(path: str) -> dict:
    item = _path(path)
    if not item.exists():
        raise ValueError("文件不存在")
    return {"type": "directory" if item.is_dir() else "file",
            "mime": mimetypes.guess_type(item.name)[0] or "unknown"}


def read_text_file(path: str) -> str:
    return _read(_path(path))


def modify_text_file(path: str, old_text: str, new_text: str) -> str:
    item = _path(path, create=True)
    content = _read(item)
    if not old_text or content.count(old_text) != 1:
        raise ValueError("待修改文字必须恰好出现一次")
    item.write_text(_text(content.replace(old_text, new_text)), encoding="utf-8")
    return "修改完成"


def create_text_file(directory: str, name: str, content: str = "") -> str:
    if Path(name).name != name or name in (".", ".."):
        raise ValueError("文件名无效")
    parent = _path(directory)
    if not parent.is_dir():
        raise ValueError("目标目录不存在")
    item = _path(str(parent / name), create=True)
    with item.open("x", encoding="utf-8") as target:
        target.write(_text(content))
    return str(item)


def create_directory(directory: str) -> str:
    item = _path(directory, create=True)
    item.mkdir(parents=True, exist_ok=False)
    return str(item)


def rename_item(path: str, new_name: str) -> str:
    item = _path(path, create=True)
    if not item.exists() or Path(new_name).name != new_name or new_name in (".", ".."):
        raise ValueError("原路径不存在或新名称无效")
    destination = _path(str(item.with_name(new_name)), create=True)
    if destination.exists():
        raise ValueError("目标已存在")
    return str(item.rename(destination))


def delete_directory(directory: str) -> str:
    item = _path(directory, create=True)
    if not item.is_dir():
        raise ValueError("目录不存在")
    shutil.rmtree(item)
    return "目录已删除"


def delete_file(path: str) -> str:
    item = _path(path, create=True)
    if not item.is_file():
        raise ValueError("文件不存在")
    item.unlink()
    return "文件已删除"


FUNCTIONS = {func.__name__: func for func in (
    get_local_date, is_current_year_leap, get_current_directory, list_directory,
    get_file_type, read_text_file, modify_text_file, create_text_file,
    create_directory, rename_item, delete_directory, delete_file)}

PROPERTIES = {
    "list_directory": {"directory": "目录，相对 Playground，默认 ."},
    "get_file_type": {"path": "文件或目录路径"},
    "read_text_file": {"path": "UTF-8 纯文本文件路径"},
    "modify_text_file": {"path": "文件路径", "old_text": "唯一匹配的原文", "new_text": "替换文字"},
    "create_text_file": {"directory": "已存在的目录", "name": "新文件名", "content": "文件内容，可留空"},
    "create_directory": {"directory": "要创建的目录路径"},
    "rename_item": {"path": "原路径", "new_name": "新文件名，不含目录"},
    "delete_directory": {"directory": "要删除的目录，包括其内容"},
    "delete_file": {"path": "要删除的文件"},
}

DESCRIPTIONS = {
    "get_local_date": "通过本机 date 命令读取当前日期",
    "is_current_year_leap": "计算当前年份是否为闰年",
    "get_current_directory": "获取可操作的当前工作目录 Playground",
    "list_directory": "列出目录中的文件与子目录",
    "get_file_type": "获取文件类型或目录类型",
    "read_text_file": "读取 UTF-8 纯文本文件内容",
    "modify_text_file": "用唯一的旧文字替换新文字",
    "create_text_file": "在指定目录创建新文本文件",
    "create_directory": "创建目录",
    "rename_item": "重命名文件或目录",
    "delete_directory": "删除目录及其全部内容",
    "delete_file": "删除文件",
}


def specs() -> list[dict]:
    result = []
    optional = {"list_directory": {"directory"}, "create_text_file": {"content"}}
    for name in FUNCTIONS:
        fields = PROPERTIES.get(name, {})
        result.append({"type": "function", "function": {"name": name,
            "description": DESCRIPTIONS[name],
            "parameters": {"type": "object", "properties": {
                field: {"type": "string", "description": desc} for field, desc in fields.items()},
                "required": [field for field in fields if field not in optional.get(name, set())],
                "additionalProperties": False}}})
    return result


def call(name: str, arguments: str) -> str:
    if name not in FUNCTIONS:
        return "错误：未知工具"
    try:
        args = json.loads(arguments) if arguments else {}
        if not isinstance(args, dict):
            raise ValueError("参数必须是对象")
        return json.dumps(FUNCTIONS[name](**args), ensure_ascii=False)
    except (ValueError, OSError, TypeError) as exc:
        return "错误：" + str(exc)
