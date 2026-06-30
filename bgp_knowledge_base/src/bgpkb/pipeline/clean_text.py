#!/usr/bin/env python3
import re
import sys
from pathlib import Path


"""Clean parsed text into Markdown-compatible plain text."""


def clean_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\bAS\s+(\d+)\b", r"AS\1", text)
    return text.strip() + "\n"


def main():
    if len(sys.argv) != 3:
        print("Usage: clean_text.py INPUT OUTPUT", file=sys.stderr)
        raise SystemExit(2)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(clean_text(src.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
