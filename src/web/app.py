"""
Agent Memory System Web API
============================
FastAPI 服务，暴露记忆管理功能的 REST 接口
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src import create_memory_manager

app = FastAPI(title="Agent Memory System API", version="2.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

manager = create_memory_manager()


class PerceiveRequest(BaseModel):
    text: str


class RememberRequest(BaseModel):
    content: str
    importance: float = 0.5
    tags: List[str] = []


class RecallRequest(BaseModel):
    query: str
    limit: int = 5


class EpisodicRequest(BaseModel):
    session_id: str
    role: str
    content: str


class SemanticRequest(BaseModel):
    fact: str
    entities: List[str] = []


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(static_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/stats")
async def stats():
    """获取记忆统计信息"""
    report = manager.get_observability_report()
    return report if isinstance(report, dict) else {"report": str(report)}


@app.post("/api/perceive")
async def perceive(req: PerceiveRequest):
    """感知输入 -> 感觉记忆 + 短期记忆"""
    manager.perceive(req.text)
    return {"status": "ok", "message": "已感知输入"}


@app.post("/api/remember")
async def remember(req: RememberRequest):
    """主动记忆 -> 工作记忆"""
    tags = set(req.tags) if req.tags else set()
    manager.remember(req.content, importance=req.importance, tags=tags)
    return {"status": "ok", "message": "已记录记忆"}


@app.post("/api/recall")
async def recall(req: RecallRequest):
    """回忆检索"""
    results = manager.recall(req.query, limit=req.limit)
    items = []
    for r in results:
        items.append({
            "content": r.content if hasattr(r, "content") else str(r),
            "source": getattr(r, "source", "unknown"),
            "score": getattr(r, "score", 0.0),
        })
    return {"results": items, "count": len(items)}


@app.post("/api/search")
async def search(req: RecallRequest):
    """混合检索"""
    results = manager.search_memories(req.query, limit=req.limit)
    items = []
    for r in results:
        items.append({
            "content": r.content if hasattr(r, "content") else str(r),
            "source": getattr(r, "source", "unknown"),
            "score": getattr(r, "score", 0.0),
        })
    return {"results": items, "count": len(items)}


@app.post("/api/episodic")
async def add_episodic(req: EpisodicRequest):
    """添加情景记忆"""
    manager.add_episodic(req.session_id, req.role, req.content)
    return {"status": "ok", "message": "已添加情景记忆"}


@app.post("/api/semantic")
async def add_semantic(req: SemanticRequest):
    """添加语义记忆"""
    manager.add_semantic(req.fact, entities=req.entities)
    return {"status": "ok", "message": "已添加语义记忆"}


@app.post("/api/consolidate")
async def consolidate():
    """执行记忆整合"""
    count = manager.auto_consolidate()
    return {"status": "ok", "consolidated": count}


@app.post("/api/compress")
async def compress(days: int = 7):
    """压缩旧记忆"""
    result = manager.compress_memory(days=days)
    return {"status": "ok", "compressed": result}


@app.get("/api/context")
async def get_context(query: str = "", limit: int = 10):
    """获取 LLM 上下文"""
    if query:
        context = manager.get_context_for_llm(query=query, limit=limit)
    else:
        context = manager.get_context()
    return {"context": str(context)}


@app.post("/api/save")
async def save_db(path: str = "memory.db"):
    """保存到 SQLite"""
    manager.save_to_db(path)
    return {"status": "ok", "path": path}


@app.post("/api/load")
async def load_db(path: str = "memory.db"):
    """从 SQLite 加载"""
    manager.load_from_db(path)
    return {"status": "ok", "path": path}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
