"""
Memory Store 记忆存储模块
========================

实现多层级记忆存储：
- SensoryBuffer: 感觉记忆（环形缓冲区）
- ShortTermStore: 短期记忆（容量有限）
- WorkingMemory: 工作记忆（当前任务相关）
- LongTermStore: 长期记忆（持久化）
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import deque
import json
import uuid
import hashlib


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)  # 向量嵌入
    importance: float = 0.5  # 重要性分数 0-1
    access_count: int = 0  # 访问次数
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)

    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def decay(self, hours: float = 24.0) -> float:
        """
        计算记忆衰减后的分数

        基于艾宾浩斯遗忘曲线的简化版本
        """
        time_since_access = (datetime.now() - self.last_accessed).total_seconds() / 3600
        # 衰减公式：score = importance * e^(-time/half_life)
        half_life = hours
        decay_factor = 2 ** (-time_since_access / half_life)
        return self.importance * decay_factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:100],
            "importance": self.importance,
            "access_count": self.access_count,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat()
        }


class SensoryBuffer:
    """
    感觉记忆

    特点：
    - 容量极小（7±2 项）
    - 保留时间极短（几秒）
    - 环形缓冲区实现
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(self, content: str, metadata: Dict = None) -> MemoryEntry:
        """推入新的感觉记忆"""
        entry = MemoryEntry(
            content=content,
            metadata=metadata or {},
            importance=0.1  # 感觉记忆重要性低
        )
        self.buffer.append(entry)
        return entry

    def get_all(self) -> List[MemoryEntry]:
        """获取所有感觉记忆"""
        return list(self.buffer)

    def clear(self):
        """清空感觉记忆"""
        self.buffer.clear()


class ShortTermStore:
    """
    短期记忆

    特点：
    - 容量有限（7±2 项）
    - 保留时间较短（几分钟）
    - 通过复述可转为长期记忆
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.memories: List[MemoryEntry] = []

    def add(self, content: str, importance: float = 0.5, tags: Set[str] = None) -> MemoryEntry:
        """添加短期记忆"""
        entry = MemoryEntry(
            content=content,
            importance=importance,
            tags=tags or set()
        )

        # 如果超出容量，移除最不重要的
        if len(self.memories) >= self.capacity:
            self._evict()

        self.memories.append(entry)
        return entry

    def get_recent(self, n: int = 5) -> List[MemoryEntry]:
        """获取最近的 n 条记忆"""
        return self.memories[-n:]

    def search(self, query: str) -> List[MemoryEntry]:
        """简单的关键词搜索"""
        results = []
        query_lower = query.lower()
        for mem in self.memories:
            if query_lower in mem.content.lower():
                results.append(mem)
        return results

    def _evict(self):
        """移除最不重要的记忆"""
        if not self.memories:
            return
        # 按重要性排序，移除最不重要的
        self.memories.sort(key=lambda m: m.importance)
        self.memories.pop(0)

    def clear(self):
        """清空短期记忆"""
        self.memories.clear()


class WorkingMemory:
    """
    工作记忆

    特点：
    - 存储当前任务相关的信息
    - 容量适中
    - 支持快速检索
    """

    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.memories: Dict[str, MemoryEntry] = {}  # id -> entry
        self.current_context: List[str] = []  # 当前上下文窗口

    def store(self, content: str, importance: float = 0.6, tags: Set[str] = None) -> MemoryEntry:
        """存储工作记忆"""
        entry = MemoryEntry(
            content=content,
            importance=importance,
            tags=tags or set()
        )

        if len(self.memories) >= self.capacity:
            self._evict()

        self.memories[entry.id] = entry
        return entry

    def get_context(self, limit: int = 5) -> str:
        """获取当前上下文"""
        recent = sorted(
            self.memories.values(),
            key=lambda m: m.last_accessed,
            reverse=True
        )[:limit]
        return "\n".join([m.content for m in recent])

    def update_context(self, new_item: str):
        """更新当前上下文"""
        self.current_context.append(new_item)
        if len(self.current_context) > 10:
            self.current_context.pop(0)

    def search_by_tags(self, tags: Set[str]) -> List[MemoryEntry]:
        """根据标签搜索"""
        results = []
        for mem in self.memories.values():
            if mem.tags.intersection(tags):
                results.append(mem)
        return results

    def _evict(self):
        """移除最旧的记忆"""
        if not self.memories:
            return
        oldest_id = min(self.memories.keys(), key=lambda k: self.memories[k].last_accessed)
        del self.memories[oldest_id]

    def clear(self):
        """清空工作记忆"""
        self.memories.clear()
        self.current_context.clear()


class LongTermStore:
    """
    长期记忆

    特点：
    - 容量大
    - 持久化存储
    - 基于重要性和访问频率的遗忘机制
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.memories: Dict[str, MemoryEntry] = {}

    def store(self, content: str, importance: float = 0.8, tags: Set[str] = None) -> MemoryEntry:
        """存储长期记忆"""
        entry = MemoryEntry(
            content=content,
            importance=importance,
            tags=tags or set()
        )

        # 检查是否需要清理
        if len(self.memories) >= self.max_size:
            self._forget()

        self.memories[entry.id] = entry
        return entry

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        """根据 ID 检索记忆"""
        if memory_id in self.memories:
            entry = self.memories[memory_id]
            entry.access()
            return entry
        return None

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        for mem in self.memories.values():
            # 简单的相关性计算
            relevance = 0.0
            if query_lower in mem.content.lower():
                relevance = 0.8
            elif any(tag in query_lower for tag in mem.tags):
                relevance = 0.6

            if relevance > 0:
                # 综合分数 = 相关性 * 0.6 + 重要性 * 0.2 + 新鲜度 * 0.2
                freshness = mem.decay()
                score = relevance * 0.6 + mem.importance * 0.2 + freshness * 0.2
                results.append((score, mem))

        # 排序并返回 top N
        results.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in results[:limit]]

    def _forget(self):
        """遗忘不重要的记忆"""
        if len(self.memories) < self.max_size * 0.9:
            return

        # 计算每个记忆的综合分数
        scored = []
        for mem in self.memories.values():
            score = mem.importance * 0.5 + mem.decay() * 0.3 + min(mem.access_count / 10, 0.2)
            scored.append((score, mem.id))

        # 移除分数最低的 10%
        scored.sort()
        remove_count = max(1, len(scored) // 10)
        for _, mem_id in scored[:remove_count]:
            del self.memories[mem_id]

    def clear(self):
        """清空长期记忆"""
        self.memories.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.memories:
            return {"count": 0, "avg_importance": 0}

        total_importance = sum(m.importance for m in self.memories.values())
        return {
            "count": len(self.memories),
            "avg_importance": total_importance / len(self.memories),
            "max_access": max(m.access_count for m in self.memories.values())
        }
