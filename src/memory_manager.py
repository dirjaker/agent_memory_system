"""
Memory Manager 记忆管理器
========================

统一管理多层级记忆系统，提供高级记忆操作：
- 记忆流转：感觉记忆 -> 短期记忆 -> 工作记忆 -> 长期记忆
- 记忆检索：跨层级搜索
- 记忆整合：合并相关记忆
- 遗忘机制：清理无用记忆
"""

import json
import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta

from .memory_store import (
    MemoryEntry,
    SensoryBuffer,
    ShortTermStore,
    WorkingMemory,
    LongTermStore,
    EpisodicMemory,
    SemanticMemory,
)
from .memory_consolidator import MemoryConsolidator
from .retriever import RetrievalResult

logger = logging.getLogger(__name__)


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

        # 初始化新记忆子系统
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.consolidator = MemoryConsolidator()
        self.embedding = None  # 延迟初始化

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

    # ----------------------------------------------------------
    # 新增方法：情景记忆、语义记忆、整合、检索、持久化、可观测性
    # ----------------------------------------------------------

    def auto_consolidate(self) -> int:
        """
        自动整合短期记忆到长期记忆

        使用 MemoryConsolidator 评估重要性，将重要短期记忆转入长期记忆。

        Returns:
            整合数量
        """
        count = self.consolidator.consolidate_short_to_long(
            self.short_term, self.long_term
        )
        logger.info(f"自动整合完成: {count} 条记忆从短期转入长期")
        return count

    def compress_memory(self, days: int = 7) -> int:
        """
        压缩超过 N 天的旧记忆

        使用 MemoryConsolidator 将旧记忆按日期分组并生成摘要。

        Args:
            days: 天数阈值（默认 7 天）

        Returns:
            压缩数量（压缩前条数 - 压缩后条数）
        """
        old_memories = list(self.long_term.memories.values())
        if not old_memories:
            return 0

        compressed = self.consolidator.compress_old_memories(old_memories, days=days)
        count = len(old_memories) - len(compressed)

        # 将压缩结果写回长期记忆
        if count > 0:
            self.long_term.clear()
            for mem in compressed:
                self.long_term.store(
                    content=mem.content,
                    importance=mem.importance,
                    tags=mem.tags,
                )

        logger.info(f"记忆压缩完成: 压缩了 {count} 条旧记忆")
        return count

    def get_context_for_llm(self, query: str = '', limit: int = 10) -> str:
        """
        为 LLM 生成上下文

        组合工作记忆 + 相关长期记忆 + 情景记忆 + 语义记忆，
        格式化为 LLM 可理解的文本。

        Args:
            query: 查询文本，用于检索相关记忆（空字符串则返回最近记忆）
            limit: 每类记忆的最大条数

        Returns:
            格式化的上下文文本
        """
        parts = []

        # 1. 工作记忆
        working_context = self.working.get_context(limit=min(limit, 5))
        if working_context:
            parts.append(f"[工作记忆/当前任务]\n{working_context}")

        # 2. 情景记忆（最近对话）
        recent_turns = self.episodic.get_recent_turns(n=limit)
        if recent_turns:
            turn_lines = [f"  {t.role}: {t.content}" for t in recent_turns]
            parts.append(f"[对话历史]\n" + "\n".join(turn_lines))

        # 3. 语义记忆（相关事实）
        if query:
            facts = self.semantic.search_facts(query, limit=limit)
        else:
            facts = self.semantic.get_all_facts()[:limit]
        if facts:
            fact_lines = [f"  {f.to_triple_str()}" for f in facts]
            parts.append(f"[已知事实]\n" + "\n".join(fact_lines))

        # 4. 长期记忆
        if query:
            long_term_results = self.long_term.search(query, limit=limit)
        else:
            long_term_results = sorted(
                self.long_term.memories.values(),
                key=lambda m: m.importance, reverse=True
            )[:limit]
        if long_term_results:
            lt_lines = [f"  - {m.content}" for m in long_term_results]
            parts.append(f"[长期记忆]\n" + "\n".join(lt_lines))

        if not parts:
            return ""

        return "\n\n".join(parts)

    def add_episodic(self, conversation_id: str, role: str, content: str) -> MemoryEntry:
        """
        添加情景记忆

        将对话轮次记录到情景记忆中。

        Args:
            conversation_id: 对话/会话 ID
            role: 角色（"user", "assistant", "system"）
            content: 对话内容

        Returns:
            MemoryEntry（包含对话信息的包装条目）
        """
        # 确保会话存在
        if conversation_id not in self.episodic.sessions:
            self.episodic.start_session(conversation_id)

        self.episodic.add_turn(role=role, content=content, session_id=conversation_id)

        # 同时创建一个 MemoryEntry 用于统一检索
        entry = MemoryEntry(
            content=f"[{role}] {content}",
            importance=0.5,
            tags={"episodic", conversation_id},
        )
        return entry

    def add_semantic(self, content: str, entities: Optional[List[str]] = None) -> MemoryEntry:
        """
        添加语义记忆

        将事实信息存入语义记忆。如果提供 entities，使用第一个作为主体，
        content 作为关系-客体（简单解析）。

        Args:
            content: 事实内容文本
            entities: 相关实体列表

        Returns:
            MemoryEntry
        """
        subject = entities[0] if entities else "general"
        # 将 content 作为 predicate+object 存储
        self.semantic.add_fact(
            subject=subject,
            predicate="related_to",
            obj=content,
            confidence=0.8,
            source="memory_manager",
        )

        entry = MemoryEntry(
            content=content,
            importance=0.7,
            tags={"semantic", *(entities or [])},
        )
        return entry

    def search_memories(self, query: str, limit: int = 5) -> List[RetrievalResult]:
        """
        混合检索所有记忆

        从短期、工作、长期、情景、语义记忆中搜索，
        综合打分后返回排序结果。

        Args:
            query: 搜索查询
            limit: 返回数量

        Returns:
            RetrievalResult 列表
        """
        results: List[RetrievalResult] = []
        seen_content: Set[str] = set()

        def _add(content: str, score: float, source: str):
            if content and content not in seen_content:
                seen_content.add(content)
                results.append(RetrievalResult(
                    content=content, score=score, source=source
                ))

        # 短期记忆
        for m in self.short_term.search(query):
            _add(m.content, m.importance * 0.8, "short_term")

        # 工作记忆
        for m in self.working.search_by_tags({query}):
            _add(m.content, m.importance * 0.9, "working")

        # 长期记忆
        for m in self.long_term.search(query, limit=limit):
            _add(m.content, m.importance, "long_term")

        # 情景记忆（最近对话）
        recent_turns = self.episodic.get_recent_turns(n=limit * 2)
        for turn in recent_turns:
            if query.lower() in turn.content.lower():
                _add(turn.content, 0.6, "episodic")

        # 语义记忆
        for fact in self.semantic.search_facts(query, limit=limit):
            triple_str = fact.to_triple_str()
            _add(triple_str, fact.confidence, "semantic")

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def save_to_db(self, db_path: str = 'memory.db') -> None:
        """
        保存所有记忆到 SQLite 数据库

        Args:
            db_path: 数据库文件路径
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                store TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.0,
                tags TEXT DEFAULT '[]',
                created_at TEXT,
                data TEXT
            )
        """)

        # 导出当前所有记忆
        exported = self.export_memories()

        count = 0
        for store_name in ["sensory", "short_term", "working", "long_term"]:
            for item in exported.get(store_name, []):
                cursor.execute(
                    "INSERT OR REPLACE INTO memories (id, store, content, importance, tags, created_at, data) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.get("id", ""),
                        store_name,
                        item.get("content", ""),
                        item.get("importance", 0.0),
                        json.dumps(list(item.get("tags", set()))),
                        str(item.get("created_at", "")),
                        json.dumps(item),
                    ),
                )
                count += 1

        conn.commit()
        conn.close()
        logger.info(f"保存 {count} 条记忆到 {db_path}")

    def load_from_db(self, db_path: str = 'memory.db') -> None:
        """
        从 SQLite 数据库加载记忆

        Args:
            db_path: 数据库文件路径
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT store, content, importance, tags FROM memories")
        rows = cursor.fetchall()
        conn.close()

        count = 0
        for store_name, content, importance, tags_json in rows:
            try:
                tags = set(json.loads(tags_json)) if tags_json else set()
            except (json.JSONDecodeError, TypeError):
                tags = set()

            if store_name == "short_term":
                self.short_term.add(content=content, importance=importance, tags=tags)
            elif store_name == "working":
                self.working.store(content=content, importance=importance, tags=tags)
            elif store_name == "long_term":
                self.long_term.store(content=content, importance=importance, tags=tags)
            elif store_name == "sensory":
                self.sensory.push(content)
            count += 1

        logger.info(f"从 {db_path} 加载了 {count} 条记忆")

    def get_observability_report(self) -> Dict:
        """
        生成可观测性报告

        包含各层记忆统计、整合器状态、情景/语义记忆统计。

        Returns:
            可观测性报告字典
        """
        stats = self.get_stats()

        report = {
            "memory_stats": stats.to_dict(),
            "episodic": {
                "session_count": len(self.episodic.sessions),
                "total_turns": sum(
                    len(turns) for turns in self.episodic.sessions.values()
                ),
                "current_session": self.episodic.current_session_id,
            },
            "semantic": self.semantic.get_stats(),
            "consolidator": {
                "has_llm": self.consolidator._has_llm,
                "scorer_type": type(self.consolidator._scorer).__name__,
            },
            "embedding_initialized": self.embedding is not None,
            "consolidation_threshold": self.consolidation_threshold,
        }
        return report


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
