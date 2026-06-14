# Agent Memory System - 技术文档

## 1. 项目概述

Agent Memory System 是一个智能体记忆系统，为 AI Agent 提供多层级记忆能力，使其能够：
- 记住对话历史
- 存储学到的知识
- 根据相关性检索记忆
- 自动遗忘不重要的信息

### 1.1 核心特性

- **四级记忆架构**：感觉记忆 → 短期记忆 → 工作记忆 → 长期记忆
- **记忆流转**：自动将重要记忆从短期转入长期
- **向量检索**：支持基于语义的相似度搜索
- **遗忘机制**：基于艾宾浩斯曲线的记忆衰减

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
│ Sensory Buffer  │ 感觉记忆（< 1秒）
│ 环形缓冲区       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Short-term Store│ 短期记忆（几分钟）
│ 当前对话上下文    │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Working Memory  │ 工作记忆（当前任务）
│ 活跃处理信息      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Long-term Store │ 长期记忆（持久）
│ 知识、经验        │
└─────────────────┘
```

### 2.2 记忆生命周期

```
感知(Perceive) → 编码(Encode) → 存储(Store) → 检索(Retrieve) → 遗忘(Forget)
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
```

#### 四级存储

**SensoryBuffer**
- 容量：7±2 项
- 保留时间：< 1秒
- 实现：环形缓冲区

**ShortTermStore**
- 容量：7±2 项
- 保留时间：几分钟
- 特点：支持关键词搜索

**WorkingMemory**
- 容量：20 项
- 用途：当前任务相关
- 特点：支持标签搜索

**LongTermStore**
- 容量：1000+ 项
- 保留时间：永久
- 特点：支持向量检索

### 3.2 Memory Manager (`memory_manager.py`)

统一管理四级记忆的核心类：

```python
class MemoryManager:
    def perceive(content)      # 感知输入
    def remember(content)      # 主动记忆
    def recall(query)          # 回忆检索
    def get_context()          # 获取上下文
    def consolidate()          # 整合记忆
    def forget(hours)          # 遗忘过期
```

### 3.3 Vector Store (`vector_store.py`)

向量存储实现：

```python
class SimpleVectorStore:
    def add(id, content, embedding)  # 添加文档
    def search(query_embedding)      # 向量搜索
    def search_by_text(query)        # 文本搜索
```

## 4. 使用指南

### 4.1 快速开始

```python
from src.memory_manager import create_memory_manager

# 创建记忆管理器
manager = create_memory_manager()

# 感知输入
manager.perceive("用户问：什么是 AI？")

# 主动记忆
manager.remember("AI 是人工智能", importance=0.8)

# 回忆
results = manager.recall("AI")

# 获取上下文
context = manager.get_context()
```

### 4.2 使用向量搜索

```python
from src.vector_store import create_vector_store

store = create_vector_store()

# 添加文档
store.add("doc1", "Python 是编程语言")

# 搜索
results = store.search_by_text("Python")
```

## 5. 设计决策

### 5.1 为什么选择四级记忆？

认知科学研究表明，人类记忆分为多个阶段：
- 感觉记忆：极短暂的感官输入
- 短期记忆：当前意识处理的信息
- 工作记忆：正在加工的信息
- 长期记忆：持久存储的知识

### 5.2 遗忘机制

基于艾宾浩斯遗忘曲线：
- 新记忆衰减快
- 重要记忆衰减慢
- 频繁访问的记忆更持久

### 5.3 向量嵌入

当前使用简化的哈希嵌入，实际项目应使用：
- OpenAI text-embedding-ada-002
- Sentence Transformers
- Cohere Embed

## 6. 扩展点

### 6.1 集成真实向量数据库

替换 `SimpleVectorStore` 为：
- FAISS (Facebook AI Similarity Search)
- ChromaDB
- Pinecone
- Weaviate

### 6.2 添加持久化

使用 SQLite 或 Redis 存储记忆。

### 6.3 支持多模态记忆

添加图像、音频等非文本记忆。

## 7. 已知限制

- 使用简化的向量嵌入
- 无持久化存储
- 搜索基于关键词而非语义
- 单用户设计

## 8. 后续计划

- [ ] 集成 Sentence Transformers
- [ ] 添加 SQLite 持久化
- [ ] 支持多用户记忆隔离
- [ ] 实现记忆共享机制
