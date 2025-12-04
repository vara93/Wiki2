from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from app.config import DOCS_DIR
from app.services import docs_service


@dataclass
class SearchResult:
    path: str
    title: str
    snippet: str


def _highlight(text: str, query: str) -> str:
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)


def _build_snippet(content: str, query: str, radius: int = 80) -> str:
    flat = content.replace("\n", " ")
    match = re.search(re.escape(query), flat, re.IGNORECASE)
    if not match:
        snippet = flat[: radius * 2]
    else:
        start = max(0, match.start() - radius)
        end = min(len(flat), match.end() + radius)
        snippet = flat[start:end]
    return _highlight(snippet.strip(), query)


def search(query: str) -> List[SearchResult]:
    if not query:
        return []

    results: List[SearchResult] = []
    lowered_query = query.lower()

    for md_file in DOCS_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        rel_path = md_file.relative_to(DOCS_DIR).with_suffix("").as_posix()
        filename_match = lowered_query in rel_path.lower()
        content_match = lowered_query in content.lower()
        title = docs_service.get_title_from_content(content, fallback=md_file.stem)
        title_match = lowered_query in title.lower()

        if filename_match or content_match or title_match:
            snippet = _build_snippet(content if content_match else title, query)
            results.append(SearchResult(path=rel_path, title=title, snippet=snippet))

    return results
