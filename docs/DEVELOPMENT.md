# 开发环境搭建指南

本文档介绍如何搭建 Agent Memory System 的开发环境，包括依赖安装、运行方式、代码规范等内容。

---

## 1. 环境要求

| 项目 | 要求 |
|------|------|
| Python | >= 3.8（推荐 3.12） |
| 操作系统 | macOS / Linux / Windows |
| 包管理 | pip 或 conda |

## 2. 快速搭建

### 2.1 克隆项目

```bash
git clone https://github.com/dirjaker/agent_memory_system.git
cd agent_memory_system
```

### 2.2 创建虚拟环境

**使用 conda（推荐）：**
```bash
conda create -n agent_memory_system python=3.12 -y
conda activate agent_memory_system
```

**使用 venv：**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 2.3 安装依赖

```bash
# 基础依赖（核心功能所需）
pip install -r requirements.txt

# 可选：安装 sentence-transformers（语义嵌入）
pip install sentence-transformers

# 可选：安装 scikit-learn（TF-IDF 嵌入）
pip install scikit-learn

# 可选：安装 FastAPI + Uvicorn（Web API）
pip install fastapi uvicorn

# 可选：安装 tkinter（macOS GUI，通常 Python 自带）
# macOS: brew install python-tk@3.12
```

### 2.4 验证安装

```bash
python -c "from src import create_memory_manager; m = create_memory_manager(); print('✅ 安装成功')"
```

## 3. 依赖说明

### 3.1 核心依赖（requirements.txt）

| 包 | 版本 | 用途 |
|----|------|------|
| httpx | 0.28.1 | HTTP 客户端（用于 OpenAI Embedding API） |
| pydantic | 2.13.4 | 数据校验（Web API 请求/响应模型） |
| typing_extensions | 4.15.0 | 类型注解兼容 |

### 3.2 可选依赖

| 包 | 用途 |
|----|------|
| sentence-transformers | SentenceTransformer 嵌入模型 |
| scikit-learn | TF-IDF 向量化 |
| fastapi | Web API 框架 |
| uvicorn | ASGI 服务器 |

> **注意：** 核心记忆模块（`memory_store.py`、`memory_manager.py`）仅使用 Python 标准库，无需额外安装依赖即可运行。

## 4. 运行方式

### 4.1 运行示例

```bash
# v1.0 基础演示
python examples/memory_demo.py

# v2.0 完整功能演示
python examples/enhanced_demo.py

# 向量搜索演示
python examples/vector_search.py
```

### 4.2 启动 Web API

```bash
# 方式一：直接运行
python -m src.web.app

# 方式二：使用 uvicorn
uvicorn src.web.app:app --host 0.0.0.0 --port 8081 --reload
```

启动后访问：
- 首页：`http://localhost:8081/`
- API 文档：`http://localhost:8081/docs`
- 健康检查：`http://localhost:8081/api/health`

### 4.3 启动 macOS 桌面 GUI

```bash
python -m src.macos.app
```

### 4.4 Python 代码调用

```python
from src import create_memory_manager

manager = create_memory_manager()

# 感知输入
manager.perceive("用户问：什么是 Python？")

# 主动记忆
manager.remember("Python 是一种解释型编程语言", importance=0.8, tags={"Python", "编程"})

# 混合检索
results = manager.search_memories("Python 编程")
for r in results:
    print(f"[{r.source}] {r.content} (score={r.score:.2f})")

# 持久化
manager.save_to_db("memory.db")
```

## 5. 项目结构

```
agent_memory_system/
├── src/                          # 核心源码
│   ├── __init__.py               # 包初始化，统一导出所有公共类
│   ├── memory_store.py           # 六层记忆存储实现
│   ├── memory_manager.py         # 记忆管理器（统一 API）
│   ├── memory_consolidator.py    # 记忆整合器
│   ├── retriever.py              # 混合检索器
│   ├── embedding.py              # Embedding 抽象层
│   ├── vector_store.py           # 向量存储
│   ├── persistence.py            # SQLite 持久化层
│   ├── web/
│   │   ├── app.py                # FastAPI Web API
│   │   └── static/               # 前端静态文件
│   └── macos/
│       └── app.py                # macOS 桌面 GUI
├── examples/                     # 示例代码
│   ├── memory_demo.py            # v1.0 基础演示
│   ├── enhanced_demo.py          # v2.0 完整功能演示
│   └── vector_search.py          # 向量搜索演示
├── docs/                         # 项目文档
├── assets/                       # 静态资源（banner 等）
├── packaging/
│   └── py2app_setup.py           # macOS 打包配置
├── requirements.txt              # Python 依赖
├── .gitignore                    # Git 忽略规则
├── README.md                     # 项目说明
└── REVIEW.md                     # 代码审查报告
```

## 6. 代码规范

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `MemoryManager`, `BM25Retriever` |
| 函数名 | snake_case | `create_memory_manager()`, `score_importance()` |
| 常量 | UPPER_SNAKE_CASE | `HIGH_IMPORTANCE_KEYWORDS` |
| 私有方法 | 前缀 `_` | `_evict()`, `_forget()` |

### 6.2 文档规范

- 所有公共类和方法必须有 docstring
- docstring 使用中文编写
- 复杂算法需在 docstring 中说明原理

### 6.3 类型注解

- 函数参数和返回值使用类型注解
- 使用 `typing` 模块的泛型类型

```python
from typing import List, Dict, Optional, Set

def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
    ...
```

## 7. 开发工作流

### 7.1 Git 分支

- `main`：稳定版本
- `dev`：开发分支
- 功能分支：`feature/xxx`
- 修复分支：`fix/xxx`

### 7.2 提交规范

```
<type>: <description>

类型：
- feat: 新功能
- fix: 修复
- docs: 文档
- refactor: 重构
- test: 测试
- chore: 构建/工具
```

示例：
```
feat: 添加混合检索器（BM25 + 语义）
fix: 修复 SQLite 连接泄漏问题
docs: 更新技术文档
```

## 8. 常见问题

### Q: 导入模块时报 `ModuleNotFoundError`

**A:** 确保在项目根目录下运行，或使用以下方式：
```bash
# 方式一：在项目根目录运行
cd agent_memory_system
python examples/memory_demo.py

# 方式二：安装为可编辑包
pip install -e .
```

### Q: `sentence-transformers` 安装失败

**A:** 该包依赖 PyTorch，可能需要较长时间安装。如不需要语义嵌入功能，可跳过安装，系统会自动降级为 Hash 嵌入。

### Q: Web API 的 CORS 问题

**A:** 默认只允许 `localhost` 和 `127.0.0.1`。可通过环境变量 `CORS_ORIGINS` 配置：
```bash
export CORS_ORIGINS="http://localhost:3000,http://example.com"
python -m src.web.app
```

### Q: SQLite 并发写入报错

**A:** 当前实现使用 `check_same_thread=False` 和 WAL 模式，但仍建议避免高并发写入场景。生产环境建议添加 `threading.Lock` 保护数据库操作。
