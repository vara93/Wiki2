from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Dict, Optional

from app.config import DOCS_DIR


def get_docs_root() -> Path:
    return DOCS_DIR


def normalize_path(path: str) -> str:
    clean_parts = []
    for part in PurePosixPath(path).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            continue
        clean_parts.append(part)
    return "/".join(clean_parts)


def _safe_doc_path(path: str) -> Path:
    normalized = normalize_path(path)
    if normalized == "":
        raise ValueError("Path cannot be empty")
    file_path = (DOCS_DIR / f"{normalized}.md").resolve()
    if not str(file_path).startswith(str(DOCS_DIR.resolve())):
        raise ValueError("Invalid path")
    return file_path


def list_docs_tree() -> Dict:
    root: Dict = {"name": "root", "type": "dir", "path": "", "children": []}
    nodes = {"": root}

    for dirpath, dirnames, filenames in os.walk(DOCS_DIR):
        dirnames.sort()
        filenames.sort()
        rel_dir = Path(dirpath).relative_to(DOCS_DIR)
        key = rel_dir.as_posix() if str(rel_dir) != "." else ""
        current = nodes[key]

        for dirname in dirnames:
            child_key = f"{key}/{dirname}" if key else dirname
            node = {"name": dirname, "type": "dir", "path": child_key, "children": []}
            nodes[child_key] = node
            current.setdefault("children", []).append(node)

        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            name = Path(filename).stem
            file_path = (rel_dir / name).as_posix() if str(rel_dir) != "." else name
            current.setdefault("children", []).append({
                "name": name,
                "type": "file",
                "path": file_path,
            })

    return root


def read_doc(path: str) -> Optional[str]:
    try:
        file_path = _safe_doc_path(path)
    except ValueError:
        return None
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8")


def save_doc(path: str, content: str) -> None:
    normalized = normalize_path(path)
    file_path = _safe_doc_path(normalized)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def delete_doc(path: str) -> None:
    file_path = _safe_doc_path(path)
    if file_path.exists():
        file_path.unlink()
        cleanup_empty_dirs(file_path.parent)


def delete_dir(path: str) -> None:
    normalized = normalize_path(path)
    if normalized == "":
        raise ValueError("Cannot delete root directory")
    dir_path = (DOCS_DIR / normalized).resolve()
    if not str(dir_path).startswith(str(DOCS_DIR.resolve())):
        raise ValueError("Invalid directory path")
    if dir_path.exists():
        # only remove if empty to avoid destructive operations
        if any(dir_path.iterdir()):
            raise ValueError("Directory is not empty")
        dir_path.rmdir()
        cleanup_empty_dirs(dir_path.parent)


def get_title_from_content(content: str, fallback: Optional[str] = None) -> str:
    for line in content.splitlines():
        if line.lstrip().startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title
    return fallback or "Untitled"


def cleanup_empty_dirs(start: Path) -> None:
    current = start
    root = DOCS_DIR.resolve()
    while current != root and current.is_dir():
        try:
            next_item = current.parent
            if any(current.iterdir()):
                break
            current.rmdir()
            current = next_item
        except OSError:
            break
