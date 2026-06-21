# Agent Memory System - 技术文档

## 1. 项目概述

Agent Memory System 是一个仿认知科学的智能体记忆系统，为 AI Agent 提供六层记忆能力，使其能够：
- 记住对话历史（情景记忆）
- 存储学到的知识（语义记忆）
- 根据相关性检索记忆（混合检索：BM25 + 语义向量）
- 自动整合和压缩冗余记忆
- 自动遗忘不重要的信息（艾宾浩斯遗忘曲线）

### 1.1 核心特性

- **六层记忆架构**：感觉记忆 → 短期记忆 → 工作记忆 → 长期记忆 → 情景记忆 → 语义记忆
- **记忆流转**：自动将重要记忆从短期转入长期
- **混合检索**：BM25 关键词检索 + 语义向量检索，RRF 融合
- **Embedding 抽象层**：支持 SentenceTransformer / OpenAI / TF-IDF / Hash
- **记忆整合**：LLM 驱动的重要性评估、压缩、去重
- **遗忘机制**：基于艾宾浩斯曲线的记忆衰减
- **SQLite 持久化**：记忆数据持久化存储

### 1.2 应用场景

- 对话系统的上下文管理
- 个性化 Agent 的用户偏好记忆
- 知识库的长期记忆存储
- 多轮对话的连贯性保持

## 2. 架构设计

### 2.1 记忆层级

```
输入
  ↓
┌─────────────────┐
│ Sensory Buffer  │ 感觉记忆（< 1秒，7±2 项）
│ 环形缓冲区       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Short-term Store│ 短期记忆（几分钟，7±2 项）
│ 当前对话上下文    │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Working Memory  │ 工作记忆（当前任务，20 项）
│ 活跃处理信息      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Long-term Store │ 长期记忆（持久，1000+ 项）
│ 知识、经验        │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Episodic Memory │ 情景记忆（对话历史）
│ 按会话组织       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Semantic Memory │ 语义记忆（事实知识图谱）
│ 三元组存储       │
└─────────────────┘
```

### 2.2 记忆生命周期

```
感知(Perceive) → 编码(Encode) → 存储(Store) → 检索(Retrieve) → 整合(Consolidate) → 遗忘(Forget)
```

## 3. 模块详解

### 3.1 Memory Store (`memory_store.py`)

#### MemoryEntry
```python
@dataclass
class MemoryEntry:
    id: str                # 唯一标识
    content: str           # 记忆内容
    importance: float      # 重要性 (0-1)
    access_count: int      # 访问次数
    created_at: datetime   # 创建时间
    last_accessed: datetime # 最后访问
    tags: Set[str]         # 标签
    embedding: List[float] # 向量嵌入
```

#### 六级存储

**SensoryBuffer（感觉记忆）**
- 容量：7±2 项
- 保留时间：< 1秒
- 实现：环形缓冲区（deque）

**ShortTermStore（短期记忆）**
- 容量：7±2 项
- 保留时间：几分钟
- 特点：支持关键词搜索，重要性淘汰

**WorkingMemory（工作记忆）**
- 容量：20 项
- 用途：当前任务相关
- 特点：支持标签搜索，LRU 淘汰

**LongTermStore（长期记忆）**
- 容量：1000+ 项
- 保留时间：永久
- 特点：三因子综合评分，自动遗忘

**EpisodicMemory（情景记忆）**
- 按会话（session_id）组织对话历史
- 支持 DialogueTurn 数据结构
- 关键词搜索

**SemanticMemory（语义记忆）**
- 事实知识图谱（三元组存储）
- 支持实体搜索

### 3.2 Memory Manager (`memory_manager.py`)

统一管理六层记忆的核心类：

```python
class MemoryManager:
    def perceive(content)            # 感知输入
    def remember(content, importance) # 主动记忆
    def recall(query)                # 回忆检索
    def search_memories(query)       # 混合检索
    def add_episodic(session_id, role, content)  # 添加情景记忆
    def add_semantic(fact, entities) # 添加语义记忆
    def get_context()                # 获取上下文
    def get_context_for_llm(query)   # 为 LLM 生成上下文
    def auto_consolidate()           # 自动整合
    def compress_memory(days)        # 压缩旧记忆
    def save_to_db(path)             # 保存到 SQLite
    def load_from_db(path)           # 从 SQLite 加载
    def get_observability_report()   # 可观测性报告
```

### 3.3 Memory Consolidator (`memory_consolidator.py`)

```python
class MemoryConsolidator:
    def score_importance(content)        # 评估重要性（LLM/规则）
    def summarize(memories)              # 记忆压缩
    def deduplicate(memories, threshold) # 去重
    def consolidate_short_to_long(...)   # 整合短期到长期
    def compress_old_memories(...)       # 压缩旧记忆
```

### 3.4 Hybrid Retriever (`retriever.py`)

```python
class BM25Retriever:     # BM25 关键词检索
class SemanticRetriever: # 语义向量检索
class HybridRetriever:   # 混合检索（RRF 融合）
class Reranker:          # 重排序器
```

### 3.5 Embedding (`embedding.py`)

```python
class BaseEmbedding(ABC):                    # 抽象基类
class SentenceTransformerEmbedding:          # Sentence Transformers
class OpenAIEmbedding:                       # OpenAI API
class TFIDFEmbedding:                        # TF-IDF
class HashEmbedding:                         # 哈希（零依赖）
def create_embedding(model_type="auto"):     # 工厂函数
```

### 3.6 Persistence (`persistence.py`)

```python
class MemoryDatabase:    # SQLite 数据库管理器（WAL 模式）
class MemoryRepository:  # 记忆 CRUD + JSON 导入导出
```

### 3.7 Web API (`web/app.py`)

基于 FastAPI 的 REST API，13 个端点，支持远程记忆管理。

## 4. 使用指南

### 4.1 快速开始

```python
from src import create_memory_manager

# 创建记忆管理器
manager = create_memory_manager()

# 感知输入
manager.perceive("用户问：什么是 AI？")

# 主动记忆
manager.remember("AI 是人工智能", importance=0.8, tags={"AI", "定义"})

# 混合检索
results = manager.search_memories("AI")

# 获取 LLM 上下文
context = manager.get_context_for_llm(query="AI 相关知识")

# 持久化
manager.save_to_db("memory.db")
```

### 4.2 启动 Web API

```bash
python -m src.web.app
# 访问 http://localhost:8081/docs 查看 API 文档
```

## 5. 设计决策

### 5.1 为什么选择六层记忆？

认知科学研究表明，人类记忆分为多个阶段。六层记忆架构完整覆盖了从感知输入到知识沉淀的全过程。

### 5.2 遗忘机制

基于艾宾浩斯遗忘曲线：`score = importance × 2^(-t/T_half)`
- 新记忆衰减快
- 重要记忆衰减慢
- 频繁访问的记忆更持久
- 渐进衰减而非突然删除

### 5.3 混合检索

融合 BM25（精确匹配）和语义检索（语义理解），通过 RRF 算法融合结果。

### 5.4 Embedding 降级策略

```
SentenceTransformer → OpenAI → TF-IDF → Hash（零依赖）
```

## 6. 扩展点

### 6.1 集成真实向量数据库

替换 `SimpleVectorStore` 为：FAISS / ChromaDB / Pinecone / Weaviate

### 6.2 添加分布式记忆共享

通过 Redis 或消息队列实现多 Agent 间记忆共享。

### 6.3 支持多模态记忆

添加图像、音频等非文本记忆。

## 7. 已知限制

- `memory_store.py` 文件较大（~1300 行），建议按职责拆分
- SQLite 并发写入需要额外锁保护
- 默认使用哈希嵌入，生产环境需替换为真实嵌入模型
- 缺少单元测试覆盖

## 8. 后续计划

- [ ] 记忆可视化仪表盘
- [ ] 多 Agent 记忆共享
- [ ] 记忆导出/导入（JSON / CSV）
- [ ] 单元测试覆盖
- [ ] 拆分 `memory_store.py` 为多个模块
