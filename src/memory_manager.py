"""
Memory Manager 记忆管理器
========================

统一管理多层级记忆系统，提供高级记忆操作：
- 记忆流转：感觉记忆 -> 短期记忆 -> 工作记忆 -> 长期记忆
- 记忆检索：跨层级搜索
- 记忆整合：合并相关记忆
- 遗忘机制：清理无用记忆
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from .memory_store import (
    MemoryEntry,
    SensoryBuffer,
    ShortTermStore,
    WorkingMemory,
    LongTermStore
)


@dataclass
class MemoryStats:
    """记忆统计信息"""
    sensory_count: int = 0
    short_term_count: int = 0
    working_count: int = 0
    long_term_count: int = 0
    total_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensory": self.sensory_count,
            "short_term": self.short_term_count,
            "working": self.working_count,
            "long_term": self.long_term_count,
            "total": self.total_count
        }


class MemoryManager:
    """
    记忆管理器

    统一管理四级记忆系统：
    1. 感觉记忆（Sensory）：输入缓存
    2. 短期记忆（Short-term）：当前对话
    3. 工作记忆（Working）：当前任务
    4. 长期记忆（Long-term）：持久存储
    """

    def __init__(
        self,
        sensory_capacity: int = 7,
        short_term_capacity: int = 7,
        working_capacity: int = 20,
        long_term_capacity: int = 1000
    ):
        # 初始化四级记忆
        self.sensory = SensoryBuffer(capacity=sensory_capacity)
        self.short_term = ShortTermStore(capacity=short_term_capacity)
        self.working = WorkingMemory(capacity=working_capacity)
        self.long_term = LongTermStore(max_size=long_term_capacity)

        # 记忆流转阈值
        self.consolidation_threshold = 0.6  # 短期 -> 长期的重要性阈值

    def perceive(self, content: str, metadata: Dict = None) -> MemoryEntry:
        """
        感知输入

        将输入存入感觉记忆，并自动流转到短期记忆

        Args:
            content: 输入内容
            metadata: 元数据

        Returns:
            记忆条目
        """
        # 1. 存入感觉记忆
        sensory_entry = self.sensory.push(content, metadata)

        # 2. 自动转入短期记忆
        short_term_entry = self.short_term.add(
            content=content,
            importance=0.3,  # 初始重要性较低
            tags=set()
        )

        return short_term_entry

    def remember(self, content: str, importance: float = 0.5, tags: Set[str] = None) -> MemoryEntry:
        """
        主动记忆

        将信息存入工作记忆

        Args:
            content: 要记忆的内容
            importance: 重要性
            tags: 标签

        Returns:
            记忆条目
        """
        entry = self.working.store(
            content=content,
            importance=importance,
            tags=tags
        )

        # 高重要性记忆同时存入长期记忆
        if importance >= self.consolidation_threshold:
            self.long_term.store(
                content=content,
                importance=importance,
                tags=tags
            )

        return entry

    def recall(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        回忆

        从所有层级搜索相关记忆

        Args:
            query: 搜索查询
            limit: 返回数量

        Returns:
            相关记忆列表
        """
        results = []

        # 1. 搜索短期记忆
        short_term_results = self.short_term.search(query)
        results.extend(short_term_results)

        # 2. 搜索工作记忆
        working_results = self.working.search_by_tags({query})
        results.extend(working_results)

        # 3. 搜索长期记忆
        long_term_results = self.long_term.search(query, limit=limit)
        results.extend(long_term_results)

        # 4. 去重并按重要性排序
        seen_ids = set()
        unique_results = []
        for mem in results:
            if mem.id not in seen_ids:
                seen_ids.add(mem.id)
                unique_results.append(mem)

        unique_results.sort(key=lambda m: m.importance, reverse=True)
        return unique_results[:limit]

    def get_context(self, limit: int = 5) -> str:
        """
        获取当前上下文

        组合短期记忆和工作记忆

        Args:
            limit: 记忆条数

        Returns:
            上下文字符串
        """
        context_parts = []

        # 工作记忆上下文
        working_context = self.working.get_context(limit=3)
        if working_context:
            context_parts.append(f"[当前任务]\n{working_context}")

        # 短期记忆上下文
        recent_memories = self.short_term.get_recent(n=3)
        if recent_memories:
            recent_text = "\n".join([m.content for m in recent_memories])
            context_parts.append(f"[近期记忆]\n{recent_text}")

        return "\n\n".join(context_parts)

    def consolidate(self):
        """
        整合记忆

        将重要的短期记忆转入长期记忆
        """
        # 获取所有短期记忆
        memories = self.short_term.memories.copy()

        for mem in memories:
            # 计算综合分数
            score = mem.importance * 0.7 + mem.access_count * 0.3

            # 超过阈值的转入长期记忆
            if score >= self.consolidation_threshold:
                self.long_term.store(
                    content=mem.content,
                    importance=mem.importance,
                    tags=mem.tags
                )

    def forget(self, hours: float = 24.0):
        """
        遗忘

        清理过期的记忆

        Args:
            hours: 超过多少小时视为过期
        """
        # 清理感觉记忆
        self.sensory.clear()

        # 清理过期的短期记忆
        current_time = datetime.now()
        self.short_term.memories = [
            m for m in self.short_term.memories
            if (current_time - m.created_at).total_seconds() < hours * 3600
        ]

        # 长期记忆自动遗忘
        self.long_term._forget()

    def get_stats(self) -> MemoryStats:
        """获取记忆统计"""
        return MemoryStats(
            sensory_count=len(self.sensory.buffer),
            short_term_count=len(self.short_term.memories),
            working_count=len(self.working.memories),
            long_term_count=len(self.long_term.memories),
            total_count=(
                len(self.sensory.buffer) +
                len(self.short_term.memories) +
                len(self.working.memories) +
                len(self.long_term.memories)
            )
        )

    def export_memories(self) -> Dict[str, Any]:
        """导出所有记忆"""
        return {
            "sensory": [m.to_dict() for m in self.sensory.get_all()],
            "short_term": [m.to_dict() for m in self.short_term.memories],
            "working": [m.to_dict() for m in self.working.memories.values()],
            "long_term": [m.to_dict() for m in self.long_term.memories.values()],
            "stats": self.get_stats().to_dict()
        }

    def clear_all(self):
        """清空所有记忆"""
        self.sensory.clear()
        self.short_term.clear()
        self.working.clear()
        self.long_term.clear()


def create_memory_manager(
    sensory_capacity: int = 7,
    short_term_capacity: int = 7,
    working_capacity: int = 20,
    long_term_capacity: int = 1000
) -> MemoryManager:
    """
    创建记忆管理器的工厂函数

    Args:
        sensory_capacity: 感觉记忆容量
        short_term_capacity: 短期记忆容量
        working_capacity: 工作记忆容量
        long_term_capacity: 长期记忆容量

    Returns:
        MemoryManager 实例
    """
    return MemoryManager(
        sensory_capacity=sensory_capacity,
        short_term_capacity=short_term_capacity,
        working_capacity=working_capacity,
        long_term_capacity=long_term_capacity
    )
