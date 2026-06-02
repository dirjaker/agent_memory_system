"""
Agent Memory System
===================

智能体记忆系统，提供多层级记忆能力：

记忆类型：
1. Sensory Memory（感觉记忆）：极短暂的输入缓存
2. Short-term Memory（短期记忆）：当前对话/任务上下文
3. Working Memory（工作记忆）：当前正在处理的信息
4. Long-term Memory（长期记忆）：持久化存储的经验
5. Episodic Memory（情景记忆）：对话历史
6. Semantic Memory（语义记忆）：事实知识

记忆操作：
- 编码（Encoding）：将信息转化为记忆
- 存储（Storage）：保存记忆
- 检索（Retrieval）：根据相关性检索记忆
- 遗忘（Forgetting）：清理不重要的记忆
- 整合（Consolidation）：合并和压缩记忆

作者：dirjaker
创建日期：2026-05-30
版本：2.0.0
"""

__version__ = "2.0.0"
__author__ = "dirjaker"

# ---- 记忆存储 ----
from .memory_store import (
    MemoryEntry,
    SensoryBuffer,
    ShortTermStore,
    WorkingMemory,
    LongTermStore,
    EpisodicMemory,
    SemanticMemory,
    DialogueTurn,
    Fact,
)

# ---- 记忆管理器 ----
from .memory_manager import MemoryManager, MemoryStats, create_memory_manager

# ---- 向量存储 ----
from .vector_store import SimpleVectorStore

# ---- Embedding 嵌入 ----
from .embedding import (
    BaseEmbedding,
    SentenceTransformerEmbedding,
    OpenAIEmbedding,
    TFIDFEmbedding,
    HashEmbedding,
    create_embedding,
)

# ---- 持久化 ----
from .persistence import MemoryDatabase, MemoryRepository

# ---- 记忆整合 ----
from .memory_consolidator import MemoryConsolidator

# ---- 检索 ----
from .retriever import (
    RetrievalResult,
    BM25Retriever,
    SemanticRetriever,
    HybridRetriever,
    Reranker,
)

__all__ = [
    # 记忆存储
    "MemoryEntry",
    "SensoryBuffer",
    "ShortTermStore",
    "WorkingMemory",
    "LongTermStore",
    "EpisodicMemory",
    "SemanticMemory",
    "DialogueTurn",
    "Fact",
    # 记忆管理器
    "MemoryManager",
    "MemoryStats",
    "create_memory_manager",
    # 向量存储
    "SimpleVectorStore",
    # Embedding
    "BaseEmbedding",
    "SentenceTransformerEmbedding",
    "OpenAIEmbedding",
    "TFIDFEmbedding",
    "HashEmbedding",
    "create_embedding",
    # 持久化
    "MemoryDatabase",
    "MemoryRepository",
    # 整合
    "MemoryConsolidator",
    # 检索
    "RetrievalResult",
    "BM25Retriever",
    "SemanticRetriever",
    "HybridRetriever",
    "Reranker",
]
