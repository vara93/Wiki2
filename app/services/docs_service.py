import os
from pathlib import Path
from typing import Dict, List, Optional

from app.config import DOCS_DIR


def _safe_doc_path(path: str) -> Path:
    normalized = Path(path).with_suffix(".md")
    full_path = (DOCS_DIR / normalized).resolve()
    if not str(full_path).startswith(str(DOCS_DIR.resolve())):
        raise ValueError("Invalid path")
    return full_path


def ensure_dirs_for_path(path: str) -> None:
    file_path = _safe_doc_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)


def read_doc(path: str) -> Optional[str]:
    file_path = _safe_doc_path(path)
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8")


def save_doc(path: str, content: str) -> None:
    ensure_dirs_for_path(path)
    file_path = _safe_doc_path(path)
    file_path.write_text(content, encoding="utf-8")


def delete_doc(path: str) -> None:
    file_path = _safe_doc_path(path)
    if file_path.exists():
        file_path.unlink()


def list_docs_tree() -> List[Dict]:
    tree: List[Dict] = []
    for root, dirs, files in os.walk(DOCS_DIR):
        rel_root = Path(root).relative_to(DOCS_DIR)
        for filename in sorted(f for f in files if f.endswith(".md")):
            rel_path = rel_root / Path(filename).stem
            tree.append({
                "name": Path(filename).stem,
                "path": str(rel_path).replace(os.sep, "/"),
                "parent": str(rel_root).replace(os.sep, "/") if rel_root != Path('.') else ""
            })
    tree.sort(key=lambda x: x["path"])
    return tree
