"""
Agent Memory System macOS GUI
==============================
tkinter 桌面应用，提供记忆管理功能的图形界面
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src import create_memory_manager


class MemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agent Memory System - 记忆管理系统")
        self.root.geometry("850x650")
        self.root.configure(bg="#0d1117")
        self.manager = create_memory_manager()
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#0d1117")
        style.configure("TNotebook.Tab", background="#161b22", foreground="#c9d1d9", padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", "#58a6ff")], foreground=[("selected", "#fff")])
        style.configure("TFrame", background="#0d1117")
        style.configure("TLabel", background="#0d1117", foreground="#c9d1d9")
        style.configure("TButton", background="#238636", foreground="#fff")
        style.map("TButton", background=[("active", "#2ea043")])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 感知记忆 Tab
        perceive_frame = ttk.Frame(notebook)
        notebook.add(perceive_frame, text="感知记忆")
        ttk.Label(perceive_frame, text="输入文本 (自动存入感觉记忆 + 短期记忆):").pack(anchor=tk.W, padx=8, pady=(8,2))
        self.perceive_text = scrolledtext.ScrolledText(perceive_frame, height=6, bg="#0d1117", fg="#c9d1d9",
                                                         insertbackground="#c9d1d9", font=("Menlo", 12))
        self.perceive_text.pack(fill=tk.X, padx=8)
        ttk.Button(perceive_frame, text="感知", command=self.perceive).pack(anchor=tk.W, padx=8, pady=6)
        self.perceive_result = scrolledtext.ScrolledText(perceive_frame, height=6, bg="#161b22", fg="#c9d1d9",
                                                           font=("Menlo", 11), state=tk.DISABLED)
        self.perceive_result.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

        # 主动记忆 Tab
        remember_frame = ttk.Frame(notebook)
        notebook.add(remember_frame, text="主动记忆")
        ttk.Label(remember_frame, text="记忆内容:").pack(anchor=tk.W, padx=8, pady=(8,2))
        self.remember_text = scrolledtext.ScrolledText(remember_frame, height=4, bg="#0d1117", fg="#c9d1d9",
                                                         insertbackground="#c9d1d9", font=("Menlo", 12))
        self.remember_text.pack(fill=tk.X, padx=8)
        f = ttk.Frame(remember_frame)
        f.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(f, text="重要性:").pack(side=tk.LEFT)
        self.importance_var = tk.StringVar(value="0.7")
        tk.Entry(f, textvariable=self.importance_var, width=6, bg="#0d1117", fg="#c9d1d9",
                 insertbackground="#c9d1d9").pack(side=tk.LEFT, padx=(4,12))
        ttk.Label(f, text="标签(逗号分隔):").pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        tk.Entry(f, textvariable=self.tags_var, bg="#0d1117", fg="#c9d1d9",
                 insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(remember_frame, text="记忆", command=self.remember).pack(anchor=tk.W, padx=8, pady=6)
        self.remember_result = scrolledtext.ScrolledText(remember_frame, height=4, bg="#161b22", fg="#c9d1d9",
                                                           font=("Menlo", 11), state=tk.DISABLED)
        self.remember_result.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

        # 检索 Tab
        recall_frame = ttk.Frame(notebook)
        notebook.add(recall_frame, text="检索回忆")
        ttk.Label(recall_frame, text="查询关键词:").pack(anchor=tk.W, padx=8, pady=(8,2))
        self.recall_query = tk.Entry(recall_frame, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9",
                                      font=("Menlo", 12))
        self.recall_query.pack(fill=tk.X, padx=8)
        bf = ttk.Frame(recall_frame)
        bf.pack(anchor=tk.W, padx=8, pady=6)
        ttk.Button(bf, text="回忆检索", command=self.recall).pack(side=tk.LEFT)
        ttk.Button(bf, text="混合检索", command=self.search_memories).pack(side=tk.LEFT, padx=8)
        self.recall_result = scrolledtext.ScrolledText(recall_frame, height=12, bg="#161b22", fg="#c9d1d9",
                                                        font=("Menlo", 11), state=tk.DISABLED)
        self.recall_result.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

        # 统计 Tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="统计信息")
        ttk.Button(stats_frame, text="刷新统计", command=self.load_stats).pack(anchor=tk.W, padx=8, pady=8)
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, bg="#161b22", fg="#c9d1d9",
                                                     font=("Menlo", 11), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))

    def _set(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def perceive(self):
        text = self.perceive_text.get("1.0", tk.END).strip()
        if not text: return
        self.manager.perceive(text)
        self._set(self.perceive_result, "已感知输入，已存入感觉记忆和短期记忆")

    def remember(self):
        text = self.remember_text.get("1.0", tk.END).strip()
        if not text: return
        try:
            imp = float(self.importance_var.get())
        except ValueError:
            imp = 0.5
        tags = set(t.strip() for t in self.tags_var.get().split(",") if t.strip())
        self.manager.remember(text, importance=imp, tags=tags)
        self._set(self.remember_result, f"已记录记忆 (重要性={imp}, 标签={tags})")

    def recall(self):
        query = self.recall_query.get().strip()
        if not query: return
        results = self.manager.recall(query, limit=5)
        lines = []
        for r in results:
            content = r.content if hasattr(r, "content") else str(r)
            source = getattr(r, "source", "?")
            score = getattr(r, "score", 0)
            lines.append(f"[{source}] (score={score:.2f}) {content}")
        self._set(self.recall_result, "\n".join(lines) if lines else "未找到相关记忆")

    def search_memories(self):
        query = self.recall_query.get().strip()
        if not query: return
        results = self.manager.search_memories(query, limit=5)
        lines = []
        for r in results:
            content = r.content if hasattr(r, "content") else str(r)
            source = getattr(r, "source", "?")
            score = getattr(r, "score", 0)
            lines.append(f"[{source}] (score={score:.2f}) {content}")
        self._set(self.recall_result, "\n".join(lines) if lines else "未找到相关记忆")

    def load_stats(self):
        report = self.manager.get_observability_report()
        import json
        text = json.dumps(report, indent=2, ensure_ascii=False, default=str) if isinstance(report, dict) else str(report)
        self._set(self.stats_text, text)


def main():
    root = tk.Tk()
    MemoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
