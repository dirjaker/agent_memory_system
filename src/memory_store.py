"""
Memory Store 记忆存储模块
========================

实现多层级记忆存储：
- SensoryBuffer: 感觉记忆（环形缓冲区）
- ShortTermStore: 短期记忆（容量有限）
- WorkingMemory: 工作记忆（当前任务相关）
- LongTermStore: 长期记忆（持久化）
- EpisodicMemory: 情景记忆（对话历史）  [新增]
- SemanticMemory: 语义记忆（事实知识）  [新增]

作者：dirjaker
创建日期：2026-05-30
更新日期：2026-06-02
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
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


@dataclass
class DialogueTurn:
    """对话轮次"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class EpisodicMemory:
    """
    情景记忆（对话历史）

    特点：
    - 按对话 ID 组织对话轮次
    - 支持时间窗口查询
    - 支持对话摘要
    - 模拟人类的情景记忆能力

    情景记忆记录了"发生了什么"——具体事件和经历的序列。
    在 AI Agent 中，这对应对话历史和交互记录。
    """

    def __init__(self, max_turns_per_session: int = 200, max_sessions: int = 50):
        """
        初始化情景记忆

        Args:
            max_turns_per_session: 每个会话最大轮次数
            max_sessions: 最大会话数
        """
        self.max_turns_per_session = max_turns_per_session
        self.max_sessions = max_sessions
        # 会话 ID -> 对话轮次列表
        self.sessions: Dict[str, List[DialogueTurn]] = {}
        # 会话 ID -> 摘要
        self.session_summaries: Dict[str, str] = {}
        # 会话 ID -> 元数据
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        # 当前活跃会话 ID
        self.current_session_id: Optional[str] = None

    def start_session(self, session_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        开始新会话

        Args:
            session_id: 会话 ID（不提供则自动生成）
            metadata: 会话元数据

        Returns:
            会话 ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        self.sessions[session_id] = []
        self.session_metadata[session_id] = metadata or {}
        self.current_session_id = session_id

        # 如果会话数超过上限，移除最旧的
        if len(self.sessions) > self.max_sessions:
            oldest_id = min(
                self.sessions.keys(),
                key=lambda sid: self.sessions[sid][0].timestamp if self.sessions[sid] else datetime.min
            )
            self._remove_session(oldest_id)

        return session_id

    def add_turn(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> DialogueTurn:
        """
        添加对话轮次

        Args:
            role: 角色 ("user", "assistant", "system")
            content: 内容
            session_id: 会话 ID（不提供则使用当前会话）
            metadata: 轮次元数据

        Returns:
            DialogueTurn
        """
        sid = session_id or self.current_session_id
        if sid is None:
            sid = self.start_session()

        if sid not in self.sessions:
            self.sessions[sid] = []

        turn = DialogueTurn(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.sessions[sid].append(turn)

        # 轮次超限，移除最旧的
        if len(self.sessions[sid]) > self.max_turns_per_session:
            self.sessions[sid] = self.sessions[sid][-self.max_turns_per_session:]

        return turn

    def get_session(self, session_id: str) -> List[DialogueTurn]:
        """
        获取整个会话

        Args:
            session_id: 会话 ID

        Returns:
            对话轮次列表
        """
        return self.sessions.get(session_id, [])

    def get_recent_turns(
        self,
        n: int = 10,
        session_id: Optional[str] = None
    ) -> List[DialogueTurn]:
        """
        获取最近的 n 个对话轮次

        Args:
            n: 数量
            session_id: 会话 ID

        Returns:
            对话轮次列表
        """
        sid = session_id or self.current_session_id
        if sid is None or sid not in self.sessions:
            return []
        return self.sessions[sid][-n:]

    def get_turns_in_window(
        self,
        start: datetime,
        end: datetime,
        session_id: Optional[str] = None
    ) -> List[DialogueTurn]:
        """
        按时间窗口查询对话轮次

        Args:
            start: 开始时间
            end: 结束时间
            session_id: 会话 ID（不提供则搜索所有会话）

        Returns:
            对话轮次列表
        """
        results = []
        sessions_to_search = (
            {session_id: self.sessions[session_id]} if session_id and session_id in self.sessions
            else self.sessions
        )

        for sid, turns in sessions_to_search.items():
            for turn in turns:
                if start <= turn.timestamp <= end:
                    results.append(turn)

        results.sort(key=lambda t: t.timestamp)
        return results

    def search_content(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Tuple[str, DialogueTurn]]:
        """
        搜索对话内容

        Args:
            query: 搜索关键词
            session_id: 会话 ID（不提供则搜索所有会话）
            limit: 返回数量

        Returns:
            [(session_id, DialogueTurn), ...]
        """
        results = []
        query_lower = query.lower()
        sessions_to_search = (
            {session_id: self.sessions[session_id]} if session_id and session_id in self.sessions
            else self.sessions
        )

        for sid, turns in sessions_to_search.items():
            for turn in turns:
                if query_lower in turn.content.lower():
                    results.append((sid, turn))

        return results[:limit]

    def set_summary(self, session_id: str, summary: str):
        """设置会话摘要"""
        self.session_summaries[session_id] = summary

    def get_summary(self, session_id: str) -> Optional[str]:
        """获取会话摘要"""
        return self.session_summaries.get(session_id)

    def generate_simple_summary(self, session_id: str) -> str:
        """
        生成简单摘要（规则模式）

        提取每轮的首句，拼接为摘要。

        Args:
            session_id: 会话 ID

        Returns:
            摘要文本
        """
        turns = self.sessions.get(session_id, [])
        if not turns:
            return ""

        lines = []
        for turn in turns[-10:]:  # 最近 10 轮
            content = turn.content[:50]
            if len(turn.content) > 50:
                content += "..."
            lines.append(f"[{turn.role}] {content}")

        summary = "\n".join(lines)
        self.session_summaries[session_id] = summary
        return summary

    def get_all_session_ids(self) -> List[str]:
        """获取所有会话 ID"""
        return list(self.sessions.keys())

    def get_session_count(self) -> int:
        """获取会话总数"""
        return len(self.sessions)

    def get_total_turns(self) -> int:
        """获取总轮次数"""
        return sum(len(turns) for turns in self.sessions.values())

    def _remove_session(self, session_id: str):
        """移除会话"""
        self.sessions.pop(session_id, None)
        self.session_summaries.pop(session_id, None)
        self.session_metadata.pop(session_id, None)

    def clear(self):
        """清空所有情景记忆"""
        self.sessions.clear()
        self.session_summaries.clear()
        self.session_metadata.clear()
        self.current_session_id = None


@dataclass
class Fact:
    """事实条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    subject: str = ""  # 主体
    predicate: str = ""  # 关系/谓词
    object: str = ""  # 客体
    confidence: float = 1.0  # 置信度 0-1
    source: str = ""  # 来源
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def to_triple_str(self) -> str:
        """转换为三元组字符串"""
        return f"({self.subject}, {self.predicate}, {self.object})"


class SemanticMemory:
    """
    语义记忆（事实知识）

    特点：
    - 支持实体-关系存储（三元组: 主体-关系-客体）
    - 支持事实检索
    - 支持知识更新（新事实覆盖旧事实）
    - 模拟人类的语义记忆能力

    语义记忆存储的是"知道什么"——抽象的事实和知识。
    与情景记忆不同，语义记忆不绑定具体的时间和场景。
    """

    def __init__(self, max_facts: int = 5000):
        """
        初始化语义记忆

        Args:
            max_facts: 最大事实数
        """
        self.max_facts = max_facts
        # 事实存储
        self.facts: Dict[str, Fact] = {}
        # 索引: 实体 -> 相关事实 ID 列表
        self._entity_index: Dict[str, List[str]] = defaultdict(list)
        # 索引: 关系 -> 事实 ID 列表
        self._relation_index: Dict[str, List[str]] = defaultdict(list)

    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "",
        metadata: Dict[str, Any] = None
    ) -> Fact:
        """
        添加事实

        Args:
            subject: 主体（如 "Python"）
            predicate: 关系（如 "是一种"）
            obj: 客体（如 "编程语言"）
            confidence: 置信度
            source: 来源
            metadata: 元数据

        Returns:
            Fact 条目
        """
        # 检查是否已存在相同三元组
        existing = self.find_fact(subject, predicate, obj)
        if existing:
            # 更新置信度（取较高者）
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.source = source
                existing.updated_at = datetime.now()
            return existing

        # 超过上限，移除置信度最低的事实
        if len(self.facts) >= self.max_facts:
            self._evict()

        fact = Fact(
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            source=source,
            metadata=metadata or {}
        )

        self.facts[fact.id] = fact

        # 更新索引
        self._entity_index[subject.lower()].append(fact.id)
        self._entity_index[obj.lower()].append(fact.id)
        self._relation_index[predicate.lower()].append(fact.id)

        return fact

    def find_fact(
        self,
        subject: str,
        predicate: str,
        obj: str
    ) -> Optional[Fact]:
        """
        查找特定三元组

        Args:
            subject: 主体
            predicate: 关系
            obj: 客体

        Returns:
            Fact 或 None
        """
        subject_lower = subject.lower()
        predicate_lower = predicate.lower()
        object_lower = obj.lower()

        for fact in self.facts.values():
            if (fact.subject.lower() == subject_lower and
                fact.predicate.lower() == predicate_lower and
                fact.object.lower() == object_lower):
                return fact
        return None

    def query_by_entity(
        self,
        entity: str,
        limit: int = 20
    ) -> List[Fact]:
        """
        按实体查询相关事实

        Args:
            entity: 实体名称
            limit: 返回数量

        Returns:
            Fact 列表
        """
        entity_lower = entity.lower()
        fact_ids = self._entity_index.get(entity_lower, [])
        results = []
        for fid in fact_ids:
            if fid in self.facts:
                results.append(self.facts[fid])
        return results[:limit]

    def query_by_relation(
        self,
        predicate: str,
        limit: int = 20
    ) -> List[Fact]:
        """
        按关系查询事实

        Args:
            predicate: 关系名称
            limit: 返回数量

        Returns:
            Fact 列表
        """
        pred_lower = predicate.lower()
        fact_ids = self._relation_index.get(pred_lower, [])
        results = []
        for fid in fact_ids:
            if fid in self.facts:
                results.append(self.facts[fid])
        return results[:limit]

    def query_by_triple_pattern(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
        limit: int = 20
    ) -> List[Fact]:
        """
        按三元组模式查询

        用 None 表示通配符。例如:
        - (subject="Python", predicate=None, object=None): 查找 Python 的所有事实
        - (subject=None, predicate="是", object="编程语言"): 查找所有是编程语言的实体

        Args:
            subject: 主体（None=通配）
            predicate: 关系（None=通配）
            obj: 客体（None=通配）
            limit: 返回数量

        Returns:
            Fact 列表
        """
        results = []
        for fact in self.facts.values():
            match = True
            if subject and fact.subject.lower() != subject.lower():
                match = False
            if predicate and fact.predicate.lower() != predicate.lower():
                match = False
            if obj and fact.object.lower() != obj.lower():
                match = False
            if match:
                results.append(fact)

        # 按置信度排序
        results.sort(key=lambda f: f.confidence, reverse=True)
        return results[:limit]

    def search_facts(self, keyword: str, limit: int = 20) -> List[Fact]:
        """
        搜索事实内容

        Args:
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            Fact 列表
        """
        keyword_lower = keyword.lower()
        results = []
        for fact in self.facts.values():
            if (keyword_lower in fact.subject.lower() or
                keyword_lower in fact.predicate.lower() or
                keyword_lower in fact.object.lower()):
                results.append(fact)

        results.sort(key=lambda f: f.confidence, reverse=True)
        return results[:limit]

    def update_fact(
        self,
        fact_id: str,
        new_object: Optional[str] = None,
        new_confidence: Optional[float] = None,
        new_source: Optional[str] = None
    ) -> bool:
        """
        更新事实

        Args:
            fact_id: 事实 ID
            new_object: 新客体
            new_confidence: 新置信度
            new_source: 新来源

        Returns:
            是否成功更新
        """
        fact = self.facts.get(fact_id)
        if not fact:
            return False

        if new_object is not None:
            # 移除旧索引
            old_obj_lower = fact.object.lower()
            if fact_id in self._entity_index.get(old_obj_lower, []):
                self._entity_index[old_obj_lower].remove(fact_id)
            # 更新
            fact.object = new_object
            self._entity_index[new_object.lower()].append(fact_id)

        if new_confidence is not None:
            fact.confidence = new_confidence
        if new_source is not None:
            fact.source = new_source

        fact.updated_at = datetime.now()
        return True

    def delete_fact(self, fact_id: str) -> bool:
        """
        删除事实

        Args:
            fact_id: 事实 ID

        Returns:
            是否成功删除
        """
        fact = self.facts.pop(fact_id, None)
        if not fact:
            return False

        # 清理索引
        subject_lower = fact.subject.lower()
        object_lower = fact.object.lower()
        predicate_lower = fact.predicate.lower()

        for idx in [self._entity_index.get(subject_lower, []),
                     self._entity_index.get(object_lower, []),
                     self._relation_index.get(predicate_lower, [])]:
            if fact_id in idx:
                idx.remove(fact_id)

        return True

    def get_all_facts(self) -> List[Fact]:
        """获取所有事实"""
        return list(self.facts.values())

    def get_triples_as_strings(self) -> List[str]:
        """获取所有三元组的字符串表示"""
        return [f.to_triple_str() for f in self.facts.values()]

    def get_entity_count(self) -> int:
        """获取实体数量"""
        return len(self._entity_index)

    def get_relation_count(self) -> int:
        """获取关系类型数量"""
        return len(self._relation_index)

    def _evict(self):
        """移除置信度最低的事实"""
        if len(self.facts) < self.max_facts * 0.9:
            return

        sorted_facts = sorted(self.facts.values(), key=lambda f: f.confidence)
        remove_count = max(1, len(sorted_facts) // 10)
        for fact in sorted_facts[:remove_count]:
            self.delete_fact(fact.id)

    def clear(self):
        """清空所有语义记忆"""
        self.facts.clear()
        self._entity_index.clear()
        self._relation_index.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "fact_count": len(self.facts),
            "entity_count": self.get_entity_count(),
            "relation_count": self.get_relation_count(),
            "avg_confidence": (
                sum(f.confidence for f in self.facts.values()) / len(self.facts)
                if self.facts else 0
            )
        }


# ==============================================================================
# 扩展记忆类（简化接口版本）
# ==============================================================================

class EpisodicMemory:
    """
    情景记忆（对话历史）- 简化接口版本

    特点：
    - 按对话 ID 组织对话轮次
    - 返回 MemoryEntry 格式，便于与其他记忆层统一接口
    - 支持对话摘要生成

    与上方 DialogueTurn 版本不同，此类使用 MemoryEntry 作为存储单元，
    并提供更简洁的 API 接口。
    """

    def __init__(self, max_episodes: int = 100):
        """
        初始化情景记忆

        Args:
            max_episodes: 最大对话数量
        """
        self.max_episodes = max_episodes
        # conversation_id -> 对话条目列表
        self.conversations: Dict[str, List[MemoryEntry]] = {}

    def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Dict = None
    ) -> MemoryEntry:
        """
        添加对话轮次

        Args:
            conversation_id: 对话 ID
            role: 角色（如 "user", "assistant", "system"）
            content: 对话内容
            metadata: 附加元数据

        Returns:
            MemoryEntry
        """
        if conversation_id not in self.conversations:
            # 超过上限时移除最旧的对话
            if len(self.conversations) >= self.max_episodes:
                oldest_id = min(
                    self.conversations.keys(),
                    key=lambda cid: self.conversations[cid][0].created_at
                    if self.conversations[cid] else datetime.min
                )
                del self.conversations[oldest_id]
            self.conversations[conversation_id] = []

        entry = MemoryEntry(
            content=content,
            metadata={**(metadata or {}), "role": role, "conversation_id": conversation_id},
            importance=0.6
        )
        self.conversations[conversation_id].append(entry)
        return entry

    def get_conversation(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        获取指定对话的最近条目

        Args:
            conversation_id: 对话 ID
            limit: 返回的条目数量

        Returns:
            MemoryEntry 列表
        """
        entries = self.conversations.get(conversation_id, [])
        return entries[-limit:]

    def get_recent_conversations(self, n: int = 5) -> List[str]:
        """
        返回最近活跃的对话 ID

        Args:
            n: 返回数量

        Returns:
            对话 ID 列表（按最近活跃时间降序）
        """
        if not self.conversations:
            return []

        sorted_ids = sorted(
            self.conversations.keys(),
            key=lambda cid: self.conversations[cid][-1].created_at
            if self.conversations[cid] else datetime.min,
            reverse=True
        )
        return sorted_ids[:n]

    def summarize_conversation(self, conversation_id: str) -> str:
        """
        生成对话摘要

        提取每轮内容的前 50 字符，拼接为摘要。

        Args:
            conversation_id: 对话 ID

        Returns:
            摘要文本
        """
        entries = self.conversations.get(conversation_id, [])
        if not entries:
            return ""

        lines = []
        for entry in entries[-10:]:
            role = entry.metadata.get("role", "unknown")
            text = entry.content[:50]
            if len(entry.content) > 50:
                text += "..."
            lines.append(f"[{role}] {text}")

        return "\n".join(lines)

    def search(
        self,
        query: str,
        conversation_id: str = None
    ) -> List[MemoryEntry]:
        """
        搜索对话内容

        Args:
            query: 搜索关键词
            conversation_id: 限定对话 ID（None 则搜索全部对话）

        Returns:
            匹配的 MemoryEntry 列表
        """
        results = []
        query_lower = query.lower()

        if conversation_id:
            entries = self.conversations.get(conversation_id, [])
            for entry in entries:
                if query_lower in entry.content.lower():
                    entry.access()
                    results.append(entry)
        else:
            for entries in self.conversations.values():
                for entry in entries:
                    if query_lower in entry.content.lower():
                        entry.access()
                        results.append(entry)

        return results

    def clear_conversation(self, conversation_id: str) -> None:
        """
        清空指定对话

        Args:
            conversation_id: 对话 ID
        """
        self.conversations.pop(conversation_id, None)

    def clear(self):
        """清空所有情景记忆"""
        self.conversations.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_turns = sum(len(entries) for entries in self.conversations.values())
        return {
            "conversation_count": len(self.conversations),
            "total_turns": total_turns,
        }


class SemanticMemory:
    """
    语义记忆（事实知识）- 简化接口版本

    特点：
    - 基于 MemoryEntry 的事实存储
    - 支持实体索引，快速按实体查找相关事实
    - 支持关键词搜索
    - 与上方三元组版 SemanticMemory 不同，此类使用扁平的文本+实体模型

    语义记忆存储的是"知道什么"——抽象的事实和知识。
    """

    def __init__(self, max_facts: int = 500):
        """
        初始化语义记忆

        Args:
            max_facts: 最大事实数量
        """
        self.max_facts = max_facts
        # fact_id -> 事实条目
        self.facts: Dict[str, MemoryEntry] = {}
        # entity -> 关联的 fact_id 集合
        self.entities: Dict[str, Set[str]] = defaultdict(set)

    def add_fact(
        self,
        content: str,
        entities: List[str] = None,
        importance: float = 0.8
    ) -> MemoryEntry:
        """
        添加事实

        Args:
            content: 事实内容
            entities: 相关实体列表
            importance: 重要性分数

        Returns:
            MemoryEntry
        """
        # 超过上限时移除不重要的事实
        if len(self.facts) >= self.max_facts:
            self._evict()

        entry = MemoryEntry(
            content=content,
            importance=importance,
            metadata={"entities": entities or []}
        )
        self.facts[entry.id] = entry

        # 更新实体索引
        for entity in (entities or []):
            self.entities[entity.lower()].add(entry.id)

        return entry

    def get_facts_by_entity(self, entity: str) -> List[MemoryEntry]:
        """
        按实体查找相关事实

        Args:
            entity: 实体名称

        Returns:
            MemoryEntry 列表
        """
        fact_ids = self.entities.get(entity.lower(), set())
        results = []
        for fid in fact_ids:
            if fid in self.facts:
                entry = self.facts[fid]
                entry.access()
                results.append(entry)
        # 按重要性降序
        results.sort(key=lambda e: e.importance, reverse=True)
        return results

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        搜索事实

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            匹配的 MemoryEntry 列表
        """
        query_lower = query.lower()
        results = []
        for entry in self.facts.values():
            if query_lower in entry.content.lower():
                entry.access()
                results.append(entry)

        # 按综合分数排序：相关性 + 重要性 + 新鲜度
        results.sort(key=lambda e: e.importance * 0.5 + e.decay() * 0.5, reverse=True)
        return results[:limit]

    def update_fact(self, fact_id: str, content: str) -> bool:
        """
        更新事实内容

        Args:
            fact_id: 事实 ID
            content: 新内容

        Returns:
            是否成功更新
        """
        entry = self.facts.get(fact_id)
        if not entry:
            return False

        entry.content = content
        entry.last_accessed = datetime.now()
        return True

    def delete_fact(self, fact_id: str) -> bool:
        """
        删除事实

        Args:
            fact_id: 事实 ID

        Returns:
            是否成功删除
        """
        entry = self.facts.pop(fact_id, None)
        if not entry:
            return False

        # 清理实体索引
        for entity_list in self.entities.values():
            entity_list.discard(fact_id)

        return True

    def get_all_entities(self) -> List[str]:
        """
        获取所有实体

        Returns:
            实体名称列表
        """
        return list(self.entities.keys())

    def _evict(self):
        """移除最不重要的事实"""
        if len(self.facts) < self.max_facts * 0.9:
            return

        scored = [(entry.importance, entry.id) for entry in self.facts.values()]
        scored.sort()
        remove_count = max(1, len(scored) // 10)
        for _, fid in scored[:remove_count]:
            self.delete_fact(fid)

    def clear(self):
        """清空所有语义记忆"""
        self.facts.clear()
        self.entities.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "fact_count": len(self.facts),
            "entity_count": len(self.entities),
            "avg_importance": (
                sum(e.importance for e in self.facts.values()) / len(self.facts)
                if self.facts else 0
            )
        }
