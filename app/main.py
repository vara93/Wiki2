from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown2

from app.config import DOCS_DIR, UPLOADS_DIR
from app.services import docs_service, search_service, upload_service

app = FastAPI(title="Internal Wiki")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return RedirectResponse(url="/docs")


@app.get("/docs", response_class=HTMLResponse)
async def list_docs(request: Request):
    docs_tree = docs_service.list_docs_tree()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "docs_tree": docs_tree},
    )


@app.get("/docs/new", response_class=HTMLResponse)
async def new_doc_form(request: Request):
    docs_tree = docs_service.list_docs_tree()
    return templates.TemplateResponse("new_doc.html", {"request": request, "docs_tree": docs_tree})


@app.post("/docs/new")
async def create_doc(path: str = Form(...), title: Optional[str] = Form(None), content: str = Form("")):
    if title:
        content = f"# {title}\n\n{content}"
    docs_service.save_doc(path, content)
    return RedirectResponse(url=f"/docs/{path}", status_code=303)


@app.get("/docs/{path:path}", response_class=HTMLResponse)
async def view_doc(path: str, request: Request):
    docs_tree = docs_service.list_docs_tree()
    content = docs_service.read_doc(path)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    html_content = markdown2.markdown(content, extras=["fenced-code-blocks", "tables", "toc", "code-friendly"])
    return templates.TemplateResponse(
        "view_doc.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "path": path,
            "html_content": html_content,
            "raw_content": content,
        },
    )


@app.get("/docs/{path:path}/edit", response_class=HTMLResponse)
async def edit_doc_form(path: str, request: Request):
    docs_tree = docs_service.list_docs_tree()
    content = docs_service.read_doc(path)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return templates.TemplateResponse(
        "edit_doc.html",
        {"request": request, "docs_tree": docs_tree, "path": path, "content": content},
    )


@app.post("/docs/{path:path}/edit")
async def update_doc(path: str, content: str = Form(...)):
    docs_service.save_doc(path, content)
    return RedirectResponse(url=f"/docs/{path}", status_code=303)


@app.post("/docs/{path:path}/delete")
async def remove_doc(path: str):
    docs_service.delete_doc(path)
    return RedirectResponse(url="/docs", status_code=303)


@app.get("/search", response_class=HTMLResponse)
async def search_docs(request: Request, query: str = ""):
    docs_tree = docs_service.list_docs_tree()
    results = search_service.search(query)
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "docs_tree": docs_tree, "results": results, "query": query},
    )


@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    docs_tree = docs_service.list_docs_tree()
    return templates.TemplateResponse("upload_image.html", {"request": request, "docs_tree": docs_tree, "filename": None, "url": None})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    docs_tree = docs_service.list_docs_tree()
    filename, _ = upload_service.save_upload(file)
    url = f"/uploads/{filename}"
    return templates.TemplateResponse(
        "upload_image.html",
        {
            "request": request,
            "docs_tree": docs_tree,
            "filename": filename,
            "url": url,
        },
    )
