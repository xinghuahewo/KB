#!/usr/bin/env python3
import json
import logging
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
REPORT = paths.report_path("parse_report")
BUNDLED_PYTHON_PACKAGES = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python"
logging.getLogger("pypdf").setLevel(logging.ERROR)


class TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.title_parts = []
        self.in_ignored = False
        self.ignore_depth = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.in_ignored = True
            self.ignore_depth += 1
            return
        if tag == "title":
            self.in_title = True
        if tag in {"p", "br", "div", "section", "article", "header", "footer", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.ignore_depth:
            self.ignore_depth -= 1
            self.in_ignored = self.ignore_depth > 0
            return
        if tag == "title":
            self.in_title = False
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_ignored:
            return
        if self.in_title:
            self.title_parts.append(data)
        self.parts.append(data)


def normalize_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_title(text, fallback):
    title = re.sub(r"\s+", " ", normalize_text(text)).strip()
    return title or fallback


def normalize_yaml_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_rfc_sections(text):
    sections = []
    pattern = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+([A-Z][^\n]{2,120})$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        return [{"section_id": "full", "heading": "Full Text", "content": text}]
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append({
            "section_id": match.group(1).rstrip("."),
            "heading": match.group(2).strip(),
            "content": text[start:end].strip(),
        })
    return [section for section in sections if section["content"]]


def parse_txt(path, doc_id):
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = normalize_text(raw)
    title = normalize_title(next((line.strip() for line in text.splitlines() if line.strip()), ""), doc_id)
    return {
        "doc_id": doc_id,
        "source_path": str(path.relative_to(ROOT)),
        "source_format": "txt",
        "title": title,
        "sections": split_rfc_sections(text),
    }, text


def parse_html(path, doc_id):
    raw = path.read_text(encoding="utf-8", errors="replace")
    parser = TextHTMLParser()
    parser.feed(raw)
    text = normalize_text(" ".join(parser.parts))
    title = normalize_title(" ".join(parser.title_parts), doc_id)
    sections = [{"section_id": "full", "heading": title, "content": text}]
    return {
        "doc_id": doc_id,
        "source_path": str(path.relative_to(ROOT)),
        "source_format": "html",
        "title": title,
        "sections": sections,
    }, text


def split_yaml_sections(text):
    matches = list(re.finditer(r"^([A-Za-z0-9_-]+):\s*$", text, flags=re.MULTILINE))
    if not matches:
        return [{"section_id": "full", "heading": "Full Text", "content": text}]
    sections = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = match.group(1)
        sections.append({
            "section_id": key,
            "heading": key,
            "content": text[start:end].strip(),
        })
    return [section for section in sections if section["content"]]


def parse_yaml(path, doc_id):
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = normalize_yaml_text(raw)
    title_match = re.search(r"^\s*title:\s*(.+)$", text, flags=re.MULTILINE)
    version_match = re.search(r"^\s*version:\s*(.+)$", text, flags=re.MULTILINE)
    title_parts = [title_match.group(1).strip()] if title_match else []
    if version_match:
        title_parts.append(f"version {version_match.group(1).strip()}")
    title = normalize_title(" ".join(title_parts), doc_id)
    return {
        "doc_id": doc_id,
        "source_path": str(path.relative_to(ROOT)),
        "source_format": "yaml",
        "title": title,
        "sections": split_yaml_sections(text),
    }, text


def load_pypdf():
    try:
        from pypdf import PdfReader
        return PdfReader, ""
    except ImportError:
        bundled_paths = [BUNDLED_PYTHON_PACKAGES]
        bundled_paths.extend(sorted(BUNDLED_PYTHON_PACKAGES.glob("lib/python*/site-packages")))
        for bundled_path in bundled_paths:
            if bundled_path.exists() and str(bundled_path) not in sys.path:
                sys.path.insert(0, str(bundled_path))
        try:
            from pypdf import PdfReader
            return PdfReader, ""
        except ImportError as exc:
            return None, f"无法加载 pypdf：{exc}"


def parse_pdf(path, doc_id):
    PdfReader, error = load_pypdf()
    if PdfReader is None:
        return None, "", error

    try:
        reader = PdfReader(str(path), strict=False)
    except Exception as exc:
        return None, "", f"PDF 打开失败：{exc}"

    sections = []
    text_parts = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            page_text = normalize_text(page.extract_text() or "")
        except Exception as exc:
            page_text = ""
            sections.append({
                "section_id": f"page-{page_index}",
                "heading": f"Page {page_index}",
                "content": f"[PDF 第 {page_index} 页文本抽取失败：{exc}]",
            })
            continue
        if not page_text:
            continue
        text_parts.append(page_text)
        sections.append({
            "section_id": f"page-{page_index}",
            "heading": f"Page {page_index}",
            "content": page_text,
        })

    text = normalize_text("\n\n".join(text_parts))
    if not text:
        return None, "", "PDF 未抽取到文本"

    metadata_title = ""
    try:
        metadata_title = str(reader.metadata.title or "") if reader.metadata else ""
    except Exception:
        metadata_title = ""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    title = normalize_title(metadata_title or first_line, doc_id)
    return {
        "doc_id": doc_id,
        "source_path": str(path.relative_to(ROOT)),
        "source_format": "pdf",
        "title": title,
        "sections": sections or [{"section_id": "full", "heading": title, "content": text}],
    }, text, ""


def write_outputs(doc, text, parsed_path, cleaned_path):
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    parsed_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cleaned_path.write_text(f"# {doc['title']}\n\n{text}\n", encoding="utf-8")


def process_file(path, parsed_subdir, cleaned_subdir):
    doc_id = path.stem
    if path.suffix == ".txt":
        doc, text = parse_txt(path, doc_id)
    elif path.suffix == ".html":
        doc, text = parse_html(path, doc_id)
    elif path.suffix in {".yaml", ".yml"}:
        doc, text = parse_yaml(path, doc_id)
    elif path.suffix == ".pdf":
        doc, text, error = parse_pdf(path, doc_id)
        if doc is None:
            return {"path": str(path.relative_to(ROOT)), "status": "skipped", "reason": error}
    else:
        return {"path": str(path.relative_to(ROOT)), "status": "skipped", "reason": f"不支持的后缀 {path.suffix}"}

    write_outputs(
        doc,
        text,
        paths.PARSED_DIR / parsed_subdir / f"{doc_id}.json",
        paths.CLEANED_DIR / cleaned_subdir / f"{doc_id}.md",
    )
    return {
        "path": str(path.relative_to(ROOT)),
        "status": "parsed",
        "reason": "",
        "sections": len(doc["sections"]),
        "chars": len(text),
    }


def main():
    targets = []
    targets.extend((path, "standards", "standards") for path in sorted((paths.RAW_DIR / "standards").glob("*.txt")))
    targets.extend((path, "data_docs", "data_docs") for path in sorted((paths.RAW_DIR / "data_docs").glob("*")))
    targets.extend((path, "data_docs", "data_docs") for path in sorted((paths.RAW_DIR / "tools_docs").glob("*")))
    targets.extend((path, "papers", "papers") for path in sorted((paths.RAW_DIR / "papers").glob("*")))
    targets.extend((path, "cases", "cases") for path in sorted((paths.RAW_DIR / "cases").glob("*")))

    results = []
    for path, parsed_subdir, cleaned_subdir in targets:
        results.append(process_file(path, parsed_subdir, cleaned_subdir))

    parsed_count = sum(1 for item in results if item["status"] == "parsed")
    skipped = [item for item in results if item["status"] == "skipped"]
    lines = [
        "# 解析报告",
        "",
        "## 范围",
        "",
        "本轮解析低风险原始格式：RFC TXT、HTML 文档、YAML/OpenAPI schema、HTML 论文页面、HTML 案例报告，以及可由 `pypdf` 确定性抽取文本的 PDF 文件。",
        "",
        "## 摘要",
        "",
        f"- 扫描目标数：{len(results)}",
        f"- 已解析：{parsed_count}",
        f"- 已跳过：{len(skipped)}",
        "",
        "## 已解析文件",
        "",
    ]
    for item in results:
        if item["status"] == "parsed":
            lines.append(f"- {item['path']}：{item['sections']} 个章节，{item['chars']} 个字符")
    lines.extend(["", "## 已跳过文件", ""])
    if skipped:
        lines.extend(f"- {item['path']}：{item['reason']}" for item in skipped)
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 说明",
        "",
        "- HTML 论文页和案例页已经作为来源文本解析，但对应记录在人审前仍保持 `pending`。",
        "- YAML/OpenAPI schema 只按顶层键做机械分段，不做 API 语义归纳。",
        "- PDF 解析只做文本抽取和按页切分，不做论文方法、案例角色、证据强度或影响范围等语义判断。",
        "- `data/generated/reports/snapshots/source_snapshots/peeringdb_api_docs_redoc_shell.html` 保留了 PeeringDB ReDoc 外壳快照；当前主来源使用其指向的 OpenAPI YAML。",
    ])

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Parsed {parsed_count}; skipped {len(skipped)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
