# Agent Memory System 版本记录

## v2.0.0 (2026-06-02)

### 🚀 v2.0 — 全面升级

#### 新增功能

- **Embedding 抽象层** (`embedding.py`)
  - `BaseEmbedding` 基类（统一接口）
  - `SentenceTransformerEmbedding` — 基于 sentence-transformers 的语义嵌入
  - `OpenAIEmbedding` — OpenAI text-embedding API
  - `TFIDFEmbedding` — TF-IDF 向量化
  - `HashEmbedding` — 哈希特征（零依赖）
  - `create_embedding()` — 工厂函数

- **SQLite 持久化层** (`persistence.py`)
  - `MemoryDatabase` — 数据库连接管理
  - `MemoryRepository` — 记忆 CRUD 操作

- **记忆整合器** (`memory_consolidator.py`)
  - `MemoryConsolidator` — 统一整合入口
  - LLM 驱动重要性评估 + 规则降级
  - 记忆压缩（旧记忆按日期分组摘要）
  - 去重器（Deduplicator）

- **混合检索器** (`retriever.py`)
  - `BM25Retriever` — 关键词检索（纯 Python 实现，无外部依赖）
  - `SemanticRetriever` — 语义向量检索
  - `HybridRetriever` — 混合检索（BM25 + 语义，RRF 融合）
  - `Reranker` — 重排序器
  - `RetrievalResult` — 检索结果数据类

- **情景记忆** (`memory_store.py`)
  - `EpisodicMemory` — 对话历史管理（按会话/对话组织）
  - `DialogueTurn` — 对话轮次

- **语义记忆** (`memory_store.py`)
  - `SemanticMemory` — 事实知识图谱（三元组存储）
  - `Fact` — 事实条目（subject-predicate-object）

#### 优化改进

- **MemoryManager 集成所有新组件**
  - `add_episodic()` — 添加情景记忆
  - `add_semantic()` — 添加语义记忆
  - `search_memories()` — 混合检索所有记忆
  - `get_context_for_llm()` — 为 LLM 生成结构化上下文
  - `auto_consolidate()` — 自动整合
  - `compress_memory()` — 压缩旧记忆
  - `save_to_db()` / `load_from_db()` — SQLite 持久化
  - `get_observability_report()` — 可观测性报告
- **向后兼容 v1.x API**：perceive / remember / recall / get_context / consolidate / forget 全部保留

#### 示例代码

- `examples/enhanced_demo.py` — v2.0 完整功能演示

---

## v1.0.0 (2026-05-30)

### 🎉 初始版本

#### 核心功能
- **Memory Store 模块**
  - MemoryEntry 记忆条目
  - SensoryBuffer 感觉记忆
  - ShortTermStore 短期记忆
  - WorkingMemory 工作记忆
  - LongTermStore 长期记忆

- **Memory Manager 模块**
  - perceive() 感知输入
  - remember() 主动记忆
  - recall() 回忆检索
  - get_context() 获取上下文
  - consolidate() 记忆整合
  - forget() 遗忘机制

- **Vector Store 模块**
  - SimpleVectorStore 向量存储
  - 余弦相似度计算
  - 文本向量搜索

#### 示例代码
- `examples/memory_demo.py` - 记忆系统演示
- `examples/vector_search.py` - 向量搜索演示

#### 文档
- `README.md` - 项目说明
- `TECHNICAL_DOC.md` - 技术文档
- `DIRECTION.md` - 方向指引
