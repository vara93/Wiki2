import re
from typing import List

from app.config import DOCS_DIR


def _extract_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def _extract_snippet(content: str, query: str, length: int = 160) -> str:
    lowered = content.lower()
    idx = lowered.find(query.lower())
    if idx == -1:
        return content[:length].strip()
    start = max(0, idx - 40)
    end = min(len(content), idx + len(query) + 120)
    snippet = content[start:end]
    return snippet.replace("\n", " ").strip()


def search(query: str) -> List[dict]:
    results = []
    if not query:
        return results

    for md_file in DOCS_DIR.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        rel_path = md_file.relative_to(DOCS_DIR)
        if query.lower() in content.lower() or query.lower() in rel_path.as_posix().lower():
            title = _extract_title(content, md_file.stem)
            snippet = _extract_snippet(content, query)
            results.append({
                "path": rel_path.with_suffix("").as_posix(),
                "title": title,
                "snippet": snippet,
            })
    return results
