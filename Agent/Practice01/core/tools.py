"""12 个教学用函数。文件操作只允许在 Playground 内。"""
import json
import mimetypes
import shutil
import subprocess
import configparser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
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


def fetchpage(url: str) -> dict:
    """用本机 curl 下载网页，用 trafilatura 提取 Markdown 正文。"""
    from trafilatura import extract

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("仅支持 HTTP 或 HTTPS 网页 URL")
    result = subprocess.run(
        ["curl.exe", "--location", "--fail", "--silent", "--show-error",
         "--max-time", "20", "--max-filesize", "1048576",
         "--proto", "=http,https", "--proto-redir", "=http,https", url],
        capture_output=True, timeout=25,
    )
    if result.returncode:
        raise ValueError("网页获取失败：" + result.stderr.decode("utf-8", errors="replace")[:300])
    if not result.stdout:
        raise ValueError("网页内容为空")
    markdown = extract(result.stdout.decode("utf-8", errors="replace"),
                       output_format="markdown", include_links=True,
                       include_tables=True, favor_precision=True)
    if not markdown:
        raise ValueError("未提取到网页正文")
    return {"url": url, "markdown": markdown[:12000]}


def searchWeb(query: str) -> list[dict]:
    """搜索网页并返回最多 5 条摘要、标题和 URL。"""
    if not query.strip():
        raise ValueError("搜索内容不能为空")
    config = configparser.ConfigParser(interpolation=None)
    config.read(Path(__file__).resolve().parents[1] / "config.ini", encoding="utf-8-sig")
    key = config.get("search", "baidu_qianfan_api_key", fallback="").strip()
    if not key or key.startswith("YOUR_"):
        raise ValueError("尚未配置百度千帆搜索 API Key；请在本地 config.ini 的 [search] 中填写 baidu_qianfan_api_key")
    body = {"messages": [{"role": "user", "content": query}],
            "search_source": "baidu_search_v2", "edition": "standard",
            "resource_type_filter": [{"type": "web", "top_k": 5}]}
    request = Request(
        "https://qianfan.baidubce.com/v2/ai_search/web_search",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise ValueError(f"百度搜索 HTTP {exc.code}；请检查 API Key、额度和请求参数") from None
    except (URLError, TimeoutError) as exc:
        raise ValueError("百度搜索网络请求失败或超时：" + str(exc.reason if isinstance(exc, URLError) else exc)) from None
    if data.get("code"):
        raise ValueError("百度搜索 API 错误：" + str(data.get("code")) + " " + str(data.get("message", ""))[:200])
    return [{"title": str(item.get("title") or ""), "url": str(item.get("url") or ""),
             "snippet": str(item.get("snippet") or item.get("content") or "")[:500]}
            for item in data.get("references", [])[:5] if isinstance(item, dict)]


FUNCTIONS = {func.__name__: func for func in (
    get_local_date, is_current_year_leap, get_current_directory, list_directory,
    get_file_type, read_text_file, modify_text_file, create_text_file,
    create_directory, rename_item, delete_directory, delete_file, fetchpage, searchWeb)}

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
    "fetchpage": {"url": "要读取的 HTTP/HTTPS 网页 URL"},
    "searchWeb": {"query": "搜索关键词或问题"},
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
    "fetchpage": "提取指定网页的正文，保留标题、段落、列表、表格和链接，返回 Markdown 与原始 URL",
    "searchWeb": "通过百度千帆搜索最新网页，返回标题、摘要和来源 URL",
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
