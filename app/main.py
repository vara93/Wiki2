from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown2

from app.config import UPLOADS_DIR
from app.services import docs_service, search_service, upload_service


def render_markdown_content(content: str) -> str:
    return markdown2.markdown(
        content,
        extras=[
            "fenced-code-blocks",
            "tables",
            "toc",
            "code-friendly",
            "strike",
            "cuddled-lists",
        ],
    )


def build_breadcrumbs(path: Optional[str]) -> list[dict]:
    breadcrumbs = [{"name": "Home", "url": "/docs"}]
    if not path:
        return breadcrumbs
    segments = path.strip("/").split("/")
    accumulated = []
    for segment in segments:
        accumulated.append(segment)
        breadcrumbs.append({"name": segment, "url": f"/docs/{'/'.join(accumulated)}"})
    return breadcrumbs


app = FastAPI(
    title="Internal Wiki",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


def _get_docs_tree():
    return docs_service.list_docs_tree()


def _normalize_or_400(path: str) -> str:
    normalized = docs_service.normalize_path(path)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid document path")
    return normalized


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return await list_docs(request)


@app.get("/docs", response_class=HTMLResponse)
async def list_docs(request: Request):
    docs_tree = _get_docs_tree()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "breadcrumbs": build_breadcrumbs(None),
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error"),
        },
    )


@app.get("/docs/new", response_class=HTMLResponse)
async def new_doc_form(request: Request, error: Optional[str] = None):
    docs_tree = _get_docs_tree()
    return templates.TemplateResponse(
        "new_doc.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "error": error,
            "breadcrumbs": build_breadcrumbs(None),
        },
    )


@app.post("/docs/new")
async def create_doc(
    request: Request,
    path: str = Form(...),
    title: Optional[str] = Form(None),
    content: str = Form(""),
):
    normalized_path = docs_service.normalize_path(path)
    if not normalized_path:
        docs_tree = _get_docs_tree()
        return templates.TemplateResponse(
            "new_doc.html",
            {
                "request": request,
                "docs_tree": docs_tree,
                "error": "Неверный путь документа",
                "path_value": path,
                "content": content,
                "title_value": title,
                "breadcrumbs": build_breadcrumbs(None),
            },
            status_code=400,
        )
    existing = docs_service.read_doc(normalized_path)
    if existing is not None:
        docs_tree = _get_docs_tree()
        return templates.TemplateResponse(
            "new_doc.html",
            {
                "request": request,
                "docs_tree": docs_tree,
                "error": "Документ уже существует",
                "path_value": normalized_path,
                "content": content,
                "title_value": title,
                "breadcrumbs": build_breadcrumbs(None),
            },
            status_code=400,
        )

    if title:
        content = f"# {title}\n\n{content}"
    docs_service.save_doc(normalized_path, content)
    return RedirectResponse(url=f"/docs/{normalized_path}", status_code=303)


@app.get("/docs/{path:path}", response_class=HTMLResponse)
async def view_doc(path: str, request: Request):
    normalized = _normalize_or_400(path)
    if normalized != path:
        return RedirectResponse(url=f"/docs/{normalized}", status_code=307)
    docs_tree = _get_docs_tree()
    content = docs_service.read_doc(normalized)
    breadcrumbs = build_breadcrumbs(normalized)
    if content is None:
        return templates.TemplateResponse(
            "view_doc.html",
            {
                "request": request,
                "docs_tree": docs_tree,
                "path": normalized,
                "html_content": None,
                "raw_content": None,
                "breadcrumbs": breadcrumbs,
                "error": "Документ не найден. Создайте новый или выберите другой.",
            },
            status_code=404,
        )
    html_content = render_markdown_content(content)
    return templates.TemplateResponse(
        "view_doc.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "path": normalized,
            "html_content": html_content,
            "raw_content": content,
            "breadcrumbs": breadcrumbs,
        },
    )


@app.get("/docs/{path:path}/edit", response_class=HTMLResponse)
async def edit_doc_form(path: str, request: Request):
    normalized = _normalize_or_400(path)
    if normalized != path:
        return RedirectResponse(url=f"/docs/{normalized}/edit", status_code=307)
    docs_tree = _get_docs_tree()
    content = docs_service.read_doc(normalized)
    if content is None:
        return templates.TemplateResponse(
            "view_doc.html",
            {
                "request": request,
                "docs_tree": docs_tree,
                "path": normalized,
                "html_content": None,
                "raw_content": None,
                "breadcrumbs": build_breadcrumbs(normalized),
                "error": "Документ не найден. Создайте его через форму ниже.",
            },
            status_code=404,
        )
    breadcrumbs = build_breadcrumbs(normalized)
    return templates.TemplateResponse(
        "edit_doc.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "path": normalized,
            "content": content,
            "breadcrumbs": breadcrumbs,
        },
    )


@app.post("/docs/{path:path}/edit")
async def update_doc(path: str, content: str = Form(...)):
    normalized = _normalize_or_400(path)
    docs_service.save_doc(normalized, content)
    return RedirectResponse(url=f"/docs/{normalized}", status_code=303)


@app.post("/docs/{path:path}/delete")
async def remove_doc(path: str):
    normalized = _normalize_or_400(path)
    docs_service.delete_doc(normalized)
    return RedirectResponse(url="/docs?message=Документ удален", status_code=303)


@app.post("/folders/{path:path}/delete")
async def remove_folder(path: str):
    normalized = _normalize_or_400(path)
    try:
        docs_service.delete_dir(normalized)
    except ValueError as exc:
        return RedirectResponse(
            url=f"/docs?error={exc}",
            status_code=303,
        )
    return RedirectResponse(url="/docs?message=Папка удалена", status_code=303)


@app.get("/search", response_class=HTMLResponse)
async def search_docs(request: Request, query: str = ""):
    docs_tree = _get_docs_tree()
    results = search_service.search(query)
    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "results": results,
            "query": query,
            "breadcrumbs": build_breadcrumbs(None),
        },
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    docs_tree = _get_docs_tree()
    return templates.TemplateResponse(
        "upload_image.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "filename": None,
            "url": None,
            "breadcrumbs": build_breadcrumbs(None),
        },
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    docs_tree = _get_docs_tree()
    url = upload_service.save_upload(file)
    filename = Path(url).name
    return templates.TemplateResponse(
        "upload_image.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "filename": filename,
            "url": url,
            "breadcrumbs": build_breadcrumbs(None),
        },
    )


@app.post("/render_markdown")
async def render_markdown_endpoint(request: Request):
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
        content = payload.get("content", "")
    else:
        form = await request.form()
        content = form.get("content", "")
    html = render_markdown_content(content)
    return JSONResponse({"html": html})
