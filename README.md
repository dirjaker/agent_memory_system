<div align="center">

<img src="assets/banner.svg" width="100%" alt="Agent 记忆系统">

<br>

### 🧠 Agent 记忆系统

[![Stars](https://img.shields.io/github/stars/dirjaker/agent_memory_system?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/agent_memory_system/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/agent_memory_system?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/agent_memory_system/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/agent_memory_system?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/agent_memory_system/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/agent_memory_system?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/agent_memory_system/blob/dev/LICENSE)

</div>

---

## 📖 项目简介

**Agent Memory System** 是一个仿认知科学的 AI Agent 记忆系统，为智能体提供 **六层记忆架构**（感觉 / 短期 / 工作 / 长期 / 情景 / 语义），支持记忆流转、混合检索（BM25 + 语义向量）、记忆整合压缩和基于艾宾浩斯曲线的自动遗忘机制。

> 项目灵感来源于 Atkinson-Shiffrin 记忆模型和 Baddeley 工作记忆模型，将认知科学原理工程化落地。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🧩 **六层记忆架构** | 感觉 → 短期 → 工作 → 长期 → 情景 → 语义，模拟人类认知过程 |
| ⚡ **记忆流转与整合** | 自动将重要记忆从短期转入长期，支持 LLM 驱动的重要性评估 |
| 🔍 **混合检索引擎** | BM25 关键词检索 + 语义向量检索，RRF 融合 + 重排序 |
| 🧬 **Embedding 抽象层** | 支持 SentenceTransformer / OpenAI / TF-IDF / Hash 多种嵌入方案 |
| 🗜️ **记忆压缩与去重** | 自动摘要压缩旧记忆，检测并合并重复记忆 |
| 📉 **艾宾浩斯遗忘机制** | 基于遗忘曲线的渐进衰减，重要/频繁访问的记忆保持更久 |
| 💾 **SQLite 持久化** | 记忆数据持久化存储，支持导入/导出 |
| 🌐 **Web API** | 基于 FastAPI 的 REST 接口，支持远程记忆管理 |
| 🖥️ **macOS 桌面 GUI** | 基于 tkinter 的图形界面，可视化记忆操作 |

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/dirjaker/agent_memory_system.git
cd agent_memory_system

# 创建虚拟环境
conda create -n agent_memory_system python=3.12 -y
conda activate agent_memory_system

# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/memory_demo.py
python examples/enhanced_demo.py

# 启动 Web API
python -m src.web.app
```

### Python 代码示例

```python
from src import create_memory_manager

# 创建记忆管理器
manager = create_memory_manager()

# 感知输入（自动存入感觉记忆 + 短期记忆）
manager.perceive("用户问：什么是 AI？")

# 主动记忆（高重要性自动存入长期记忆）
manager.remember("AI 是人工智能的缩写", importance=0.8, tags={"定义", "AI"})

# 混合检索
results = manager.search_memories("AI 定义")
for r in results:
    print(f"[{r.source}] {r.content} (score={r.score:.2f})")

# 生成 LLM 上下文
context = manager.get_context_for_llm(query="AI 相关知识")

# 持久化
manager.save_to_db("memory.db")
```

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│              MemoryManager（统一入口）                 │
│   perceive / remember / recall / search_memories     │
├────────┬────────┬────────┬────────┬────────┬─────────┤
│感觉记忆 │短期记忆 │工作记忆 │长期记忆 │情景记忆 │ 语义记忆 │
│Sensory │ShortTm │Working │LongTm  │Episodic│Semantic │
│Buffer  │Store   │Memory  │Store   │Memory  │Memory   │
├────────┴────────┴────────┴────────┴────────┴─────────┤
│  MemoryConsolidator（整合/压缩/去重/重要性评估）        │
│  HybridRetriever（BM25 + Semantic + Reranker）        │
│  Embedding 抽象层（ST / OpenAI / TF-IDF / Hash）      │
│  Persistence 持久化层（SQLite）                        │
└─────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **语言** | Python 3.8+ |
| **核心框架** | dataclasses, collections, abc |
| **Web 服务** | FastAPI, Uvicorn, Pydantic |
| **嵌入模型** | Sentence Transformers, OpenAI Embedding API |
| **向量存储** | 内存向量存储（可替换为 FAISS / ChromaDB） |
| **持久化** | SQLite（WAL 模式） |
| **数据校验** | Pydantic v2 |

## 📁 项目结构

```
agent_memory_system/
├── src/                          # 核心源码
│   ├── __init__.py               # 包初始化，统一导出
│   ├── memory_store.py           # 六层记忆存储实现
│   ├── memory_manager.py         # 记忆管理器（统一 API）
│   ├── memory_consolidator.py    # 记忆整合器（压缩/去重/评估）
│   ├── retriever.py              # 混合检索器（BM25/语义/Reranker）
│   ├── embedding.py              # Embedding 抽象层
│   ├── vector_store.py           # 向量存储
│   ├── persistence.py            # SQLite 持久化层
│   ├── web/app.py                # FastAPI Web API
│   └── macos/app.py              # macOS 桌面 GUI
├── examples/                     # 示例代码
│   ├── memory_demo.py            # v1.0 基础演示
│   ├── enhanced_demo.py          # v2.0 完整功能演示
│   └── vector_search.py          # 向量搜索演示
├── docs/                         # 项目文档
│   ├── 技术文档.md               # 详细技术设计文档
│   ├── DEVELOPMENT.md            # 开发环境搭建指南
│   ├── CHANGELOG.md              # 版本更新日志
│   ├── VERSION.md                # 版本记录
│   └── DIRECTION.md              # 项目方向指引
├── assets/                       # 静态资源
├── requirements.txt              # Python 依赖
└── REVIEW.md                     # 代码审查报告
```

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [技术文档](docs/技术文档.md) | 完整的系统设计文档，含架构图、模块详解、面试问答 |
| [开发指南](docs/DEVELOPMENT.md) | 开发环境搭建、运行方式、代码规范 |
| [更新日志](docs/CHANGELOG.md) | 版本迭代记录 |
| [版本记录](docs/VERSION.md) | 各版本功能清单 |
| [方向指引](docs/DIRECTION.md) | 项目定位与学习路径 |
| [代码审查](REVIEW.md) | 代码质量与安全审查报告 |

## 📝 开发路线

- [x] 六层记忆架构（感觉 / 短期 / 工作 / 长期 / 情景 / 语义）
- [x] 向量检索引擎（BM25 + 语义混合检索）
- [x] 记忆整合与压缩（LLM 驱动 + 规则降级）
- [x] Embedding 抽象层（多模型支持）
- [x] SQLite 持久化存储
- [x] FastAPI Web API
- [x] macOS 桌面 GUI
- [ ] 记忆可视化仪表盘
- [ ] 多 Agent 记忆共享
- [ ] 记忆导出/导入（JSON / CSV）
- [ ] 单元测试覆盖

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/agent_memory_system](https://github.com/dirjaker/agent_memory_system)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
