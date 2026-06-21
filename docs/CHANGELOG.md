# 更新日志

本文件记录 Agent Memory System 的所有版本更新。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [2.0.0] - 2026-06-02

### 🚀 全面升级

本次更新将系统从四层记忆架构升级为六层记忆架构，新增混合检索引擎、Embedding 抽象层、记忆整合器和 SQLite 持久化层。

### 新增

#### 记忆存储
- **情景记忆（EpisodicMemory）**：按会话管理对话历史，支持 `DialogueTurn` 数据结构
- **语义记忆（SemanticMemory）**：事实知识图谱，以三元组（subject-predicate-object）形式存储

#### Embedding 抽象层（`embedding.py`）
- `BaseEmbedding` 抽象基类，统一嵌入接口
- `SentenceTransformerEmbedding` — 基于 sentence-transformers 的语义嵌入
- `OpenAIEmbedding` — OpenAI text-embedding API 集成
- `TFIDFEmbedding` — TF-IDF 向量化
- `HashEmbedding` — 哈希特征（零依赖降级方案）
- `create_embedding()` — 工厂函数，支持自动降级

#### 混合检索器（`retriever.py`）
- `BM25Retriever` — BM25 关键词检索（Okapi BM25 算法，纯 Python 实现）
- `SemanticRetriever` — 语义向量检索
- `HybridRetriever` — 混合检索（BM25 + 语义，RRF 融合算法）
- `Reranker` — 基于查询相关性的结果重排序
- `RetrievalResult` — 统一检索结果数据类

#### 记忆整合器（`memory_consolidator.py`）
- `MemoryConsolidator` — 统一整合入口
- `RuleBasedImportanceScorer` — 基于规则的重要性评估（关键词检测、内容长度、数字密度等）
- `LLMImportanceScorer` — 基于 LLM 的重要性评估
- `summarize()` — 记忆压缩（旧记忆按日期分组摘要）
- `deduplicate()` — 重复记忆检测与合并（编辑距离相似度）

#### 持久化层（`persistence.py`）
- `MemoryDatabase` — SQLite 数据库管理器（WAL 模式）
- `MemoryRepository` — 记忆 CRUD 操作，支持 JSON 导入/导出

#### Web API（`web/app.py`）
- 基于 FastAPI 的 REST API
- 13 个 API 端点：health / stats / perceive / remember / recall / search / episodic / semantic / consolidate / compress / context / save / load

#### 桌面 GUI（`macos/app.py`）
- 基于 tkinter 的 macOS 桌面应用
- 四个标签页：感知记忆 / 主动记忆 / 检索回忆 / 统计信息

### 改进

- **MemoryManager 集成所有新组件**：新增 `add_episodic()`、`add_semantic()`、`search_memories()`、`get_context_for_llm()`、`auto_consolidate()`、`compress_memory()`、`save_to_db()`、`load_from_db()`、`get_observability_report()` 等方法
- **向后兼容 v1.x API**：perceive / remember / recall / get_context / consolidate / forget 全部保留
- 新增 `examples/enhanced_demo.py` — v2.0 完整功能演示

---

## [1.0.0] - 2026-05-30

### 🎉 初始版本

#### 核心功能

**记忆存储模块（`memory_store.py`）**
- `MemoryEntry` — 记忆条目数据类，含艾宾浩斯衰减方法
- `SensoryBuffer` — 感觉记忆（环形缓冲区，容量 7±2）
- `ShortTermStore` — 短期记忆（重要性淘汰策略）
- `WorkingMemory` — 工作记忆（LRU 淘汰，标签检索）
- `LongTermStore` — 长期记忆（三因子综合评分，自动遗忘）

**记忆管理器（`memory_manager.py`）**
- `MemoryManager` — 统一管理四级记忆
- `perceive()` — 感知输入（双写感觉记忆 + 短期记忆）
- `remember()` — 主动记忆（高重要性自动写入长期记忆）
- `recall()` — 跨层级检索（去重 + 按重要性排序）
- `get_context()` — 获取上下文（工作记忆 + 短期记忆）
- `consolidate()` — 记忆整合（短期 → 长期）
- `forget()` — 遗忘过期记忆

**向量存储（`vector_store.py`）**
- `SimpleVectorStore` — 内存向量存储
- 余弦相似度和欧氏距离计算
- `search_by_text()` — 文本向量搜索
- MD5 哈希伪嵌入（演示用）

**示例代码**
- `examples/memory_demo.py` — 记忆系统演示
- `examples/vector_search.py` — 向量搜索演示

**文档**
- `README.md` — 项目说明
- `docs/技术文档.md` — 技术设计文档
- `docs/TECHNICAL_DOC.md` — 英文技术文档
- `docs/DIRECTION.md` — 项目方向指引
- `docs/VERSION.md` — 版本记录
