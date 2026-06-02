"""
Memory Consolidator 记忆整合器
==============================

负责记忆的整合、压缩和质量评估：
- score_importance: 评估记忆重要性（LLM 或规则降级）
- summarize: 将多条记忆压缩为摘要
- deduplicate: 检测和合并重复记忆
- consolidate_short_to_long: 整合短期记忆到长期记忆
- compress_old_memories: 压缩旧记忆

支持 LLM 模式和纯规则降级模式。

作者：dirjaker
创建日期：2026-06-02
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging
import re

# 导入项目内部类型
from .memory_store import MemoryEntry, ShortTermStore, LongTermStore

logger = logging.getLogger(__name__)


# ============================================================
# 重要性评分器（策略模式）
# ============================================================

class BaseImportanceScorer(ABC):
    """重要性评分器抽象基类"""

    @abstractmethod
    def score(self, content: str, context: str = "") -> float:
        """
        评估内容的重要性

        Args:
            content: 要评估的内容
            context: 上下文信息

        Returns:
            重要性分数 0.0 - 1.0
        """
        pass


class RuleBasedImportanceScorer(BaseImportanceScorer):
    """
    基于规则的重要性评分器

    不依赖 LLM，使用启发式规则评估重要性。
    规则包括：关键词检测、内容长度、访问次数、数字密度等。
    """

    # 高重要性关键词
    HIGH_IMPORTANCE_KEYWORDS = {
        "重要", "关键", "必须", "记住", "注意", "警告", "错误", "bug", "问题",
        "决定", "结论", "结果", "方案", "计划", "目标", "任务", "密码", "账号",
        "important", "critical", "must", "warning", "error", "todo",
        "deadline", "urgent", "紧急", "牢记", "切记", "务必",
    }

    # 低重要性关键词
    LOW_IMPORTANCE_KEYWORDS = {
        "你好", "嗯", "好的", "ok", "谢谢", "hello", "hi",
        "thanks", "got it", "明白", "了解", "嗯嗯", "哈哈",
    }

    def score(self, content: str, context: str = "") -> float:
        """
        基于规则评估重要性

        评分维度：
        1. 关键词匹配（±0.3）
        2. 内容长度（0.1 - 0.2）
        3. 数字/日期密度（+0.05 ~ +0.1）
        4. 问句标记（+0.05）
        5. 感叹号（+0.05）

        Args:
            content: 记忆内容
            context: 上下文（规则模式下暂未使用）

        Returns:
            重要性分数 0.0 - 1.0
        """
        if not content or not content.strip():
            return 0.1

        score = 0.5  # 基础分
        content_lower = content.lower().strip()

        # ---- 1. 低重要性关键词：直接返回低分 ----
        for kw in self.LOW_IMPORTANCE_KEYWORDS:
            if content_lower == kw:
                return 0.15  # 极短的寒暄

        # ---- 2. 高重要性关键词 ----
        high_hits = sum(1 for kw in self.HIGH_IMPORTANCE_KEYWORDS if kw in content_lower)
        if high_hits >= 3:
            score += 0.3
        elif high_hits >= 2:
            score += 0.2
        elif high_hits >= 1:
            score += 0.1

        # ---- 3. 内容长度 ----
        length = len(content)
        if length > 300:
            score += 0.2
        elif length > 200:
            score += 0.15
        elif length > 100:
            score += 0.1
        elif length > 50:
            score += 0.05

        # ---- 4. 数字密度（包含数字/日期通常更重要） ----
        digit_count = sum(1 for c in content if c.isdigit())
        if digit_count > 5:
            score += 0.1
        elif digit_count > 2:
            score += 0.05

        # ---- 5. 问号（可能是重要问题） ----
        if "?" in content or "？" in content:
            score += 0.05

        # ---- 6. 感叹号（情感强烈） ----
        if "!" in content or "！" in content:
            score += 0.05

        return min(max(score, 0.0), 1.0)


class LLMImportanceScorer(BaseImportanceScorer):
    """
    基于 LLM 的重要性评分器

    使用大语言模型评估内容重要性。
    调用失败时自动降级为规则评分。
    """

    # 降级用的规则评分器（类级别共享）
    _fallback = RuleBasedImportanceScorer()

    def __init__(self, llm_client):
        """
        初始化

        Args:
            llm_client: LLM 客户端对象，需实现 chat(prompt: str) -> str 方法
        """
        self._client = llm_client

    def score(self, content: str, context: str = "") -> float:
        """使用 LLM 评估重要性，失败时降级为规则评分"""
        prompt = (
            "请评估以下文本的重要性，返回一个 0.0 到 1.0 之间的分数。\n"
            "0.0 = 完全不重要（如寒暄、重复内容）\n"
            "0.5 = 一般重要\n"
            "1.0 = 非常重要（关键信息、决策、任务）\n\n"
            f"文本: {content[:500]}\n"
        )
        if context:
            prompt += f"上下文: {context[:200]}\n"
        prompt += "\n只返回数字分数，不要解释。"

        try:
            response = self._client.chat(prompt)
            # 提取数字
            numbers = re.findall(r"[\d.]+", str(response))
            if numbers:
                score = float(numbers[0])
                return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.warning(f"LLM 评分失败: {e}，使用规则降级")

        # 降级到规则评分
        return self._fallback.score(content, context)


# ============================================================
# 摘要器（策略模式）
# ============================================================

class BaseSummarizer(ABC):
    """摘要器抽象基类"""

    @abstractmethod
    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """将多条文本压缩为摘要"""
        pass


class RuleBasedSummarizer(BaseSummarizer):
    """
    基于规则的摘要器

    降级方案：直接拼接前 N 条记忆的首句。
    """

    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """基于规则生成摘要：提取每条文本的首句，去重后拼接"""
        if not texts:
            return ""

        if len(texts) == 1:
            return texts[0][:max_length]

        # 提取每条文本的关键句
        key_sentences: List[str] = []
        seen: Set[str] = set()

        for text in texts:
            first_sentence = self._extract_first_sentence(text)
            normalized = first_sentence.strip().lower()
            if normalized and normalized not in seen and len(normalized) > 5:
                seen.add(normalized)
                key_sentences.append(first_sentence)

        summary = "；".join(key_sentences)

        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return summary

    @staticmethod
    def _extract_first_sentence(text: str) -> str:
        """提取第一个句子"""
        for sep in ["。", "！", "？", ".", "!", "?", "；", "\n"]:
            idx = text.find(sep)
            if 0 < idx < len(text) - 1:
                return text[: idx + 1]
        return text


class LLMSummarizer(BaseSummarizer):
    """
    基于 LLM 的摘要器

    使用大语言模型生成摘要，失败时降级为规则摘要。
    """

    _fallback = RuleBasedSummarizer()

    def __init__(self, llm_client):
        self._client = llm_client

    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """使用 LLM 生成摘要"""
        combined = "\n".join(f"- {t}" for t in texts[:20])
        prompt = (
            f"请将以下多条记忆压缩为一段简洁的摘要（不超过{max_length}字）:\n\n"
            f"{combined}\n\n摘要:"
        )

        try:
            response = self._client.chat(prompt)
            return str(response)[:max_length]
        except Exception as e:
            logger.warning(f"LLM 摘要失败: {e}，使用规则降级")
            return self._fallback.summarize(texts, max_length)


# ============================================================
# 去重器
# ============================================================

class Deduplicator:
    """
    记忆去重器

    检测和合并重复或高度相似的记忆。
    使用字符级 bigram Jaccard 相似度进行模糊匹配。
    """

    @staticmethod
    def _compute_similarity(text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        使用字符级 Jaccard 相似度（bigram）。
        """

        def get_bigrams(text: str) -> set:
            t = text.lower().strip()
            return {t[i : i + 2] for i in range(len(t) - 1)}

        if text1 == text2:
            return 1.0

        bigrams1 = get_bigrams(text1)
        bigrams2 = get_bigrams(text2)

        if not bigrams1 or not bigrams2:
            return 0.0

        intersection = bigrams1 & bigrams2
        union = bigrams1 | bigrams2

        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def _edit_distance_ratio(s1: str, s2: str) -> float:
        """
        基于编辑距离的相似度比率

        作为 Jaccard 的补充，在短文本上更准确。
        """
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # 简化版编辑距离（限制长度避免性能问题）
        max_len = 200
        a, b = s1[:max_len].lower(), s2[:max_len].lower()
        la, lb = len(a), len(b)

        # 使用滚动数组优化空间
        prev = list(range(lb + 1))
        curr = [0] * (lb + 1)

        for i in range(1, la + 1):
            curr[0] = i
            for j in range(1, lb + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                curr[j] = min(
                    prev[j] + 1,      # 删除
                    curr[j - 1] + 1,  # 插入
                    prev[j - 1] + cost # 替换
                )
            prev, curr = curr, prev

        dist = prev[lb]
        max_dist = max(la, lb)
        return 1.0 - (dist / max_dist)

    def deduplicate(
        self,
        memories: List[MemoryEntry],
        threshold: float = 0.9,
    ) -> List[MemoryEntry]:
        """
        检测和合并重复记忆

        对于高度相似的记忆对，保留重要性更高、内容更完整的那条。

        Args:
            memories: 记忆条目列表
            threshold: 相似度阈值，超过此值视为重复（默认 0.9）

        Returns:
            去重后的记忆列表
        """
        if not memories:
            return []

        n = len(memories)

        # ---- 并查集：将相似记忆归为一组 ----
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # 计算相似度并合并
        for i in range(n):
            for j in range(i + 1, n):
                # 使用两种相似度的加权平均
                jaccard = self._compute_similarity(
                    memories[i].content, memories[j].content
                )
                edit_ratio = self._edit_distance_ratio(
                    memories[i].content, memories[j].content
                )
                sim = jaccard * 0.6 + edit_ratio * 0.4
                if sim >= threshold:
                    union(i, j)

        # ---- 每组保留最佳记忆 ----
        groups: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            groups.setdefault(root, []).append(i)

        kept: List[MemoryEntry] = []
        for group_indices in groups.values():
            # 优先级：重要性 > 访问次数 > 内容长度
            best_idx = max(
                group_indices,
                key=lambda idx: (
                    memories[idx].importance,
                    memories[idx].access_count,
                    len(memories[idx].content),
                ),
            )
            kept.append(memories[best_idx])

        logger.debug(f"去重: {n} -> {len(kept)} 条（移除 {n - len(kept)} 条重复）")
        return kept


# ============================================================
# 记忆整合器（主类）
# ============================================================

class MemoryConsolidator:
    """
    记忆整合器

    统一管理记忆的重要性评估、摘要、去重、整合和压缩。
    支持 LLM 模式和纯规则降级模式。

    使用方式::

        # LLM 模式
        consolidator = MemoryConsolidator(llm_client=my_llm)

        # 规则降级模式（无 LLM）
        consolidator = MemoryConsolidator()

        # 评估重要性
        score = consolidator.score_importance("这条记忆很重要")

        # 去重
        unique = consolidator.deduplicate(memories, threshold=0.9)

        # 整合短期到长期
        count = consolidator.consolidate_short_to_long(st, lt)
    """

    def __init__(self, llm_client=None, embedding=None):
        """
        初始化记忆整合器

        Args:
            llm_client: 可选的 LLM 客户端。如果提供，使用 LLM 进行
                        重要性评估和摘要生成；否则使用纯规则方案。
                        客户端需实现 chat(prompt: str) -> str 方法。
            embedding: 可选的嵌入模型，用于向量级别的相似度计算。
                       预留接口，当前版本使用文本级相似度。
        """
        self._llm_client = llm_client
        self._embedding = embedding
        self._has_llm = llm_client is not None

        # ---- 重要性评分器 ----
        if self._has_llm:
            self._scorer: BaseImportanceScorer = LLMImportanceScorer(llm_client)
            logger.info("MemoryConsolidator 初始化: LLM 评分模式")
        else:
            self._scorer = RuleBasedImportanceScorer()
            logger.info("MemoryConsolidator 初始化: 规则评分降级模式")

        # ---- 摘要器 ----
        if self._has_llm:
            self._summarizer: BaseSummarizer = LLMSummarizer(llm_client)
        else:
            self._summarizer = RuleBasedSummarizer()

        # ---- 去重器 ----
        self._deduplicator = Deduplicator()

    # ----------------------------------------------------------
    # 公开 API
    # ----------------------------------------------------------

    def score_importance(self, content: str, context: str = "") -> float:
        """
        评估记忆重要性

        有 LLM 时调用 LLM 评分，无 LLM 时用规则降级方案：
        - 基于关键词（重要、关键、记住等）
        - 内容长度
        - 访问次数（通过 metadata 传入）

        Args:
            content: 记忆内容文本
            context: 上下文信息

        Returns:
            重要性分数 0.0 ~ 1.0
        """
        return self._scorer.score(content, context)

    def summarize(self, memories: List[MemoryEntry]) -> str:
        """
        将多条记忆压缩为摘要

        有 LLM 时调用 LLM 生成摘要，无 LLM 时降级为：
        直接拼接前 N 条记忆的首句。

        Args:
            memories: 记忆条目列表

        Returns:
            摘要文本
        """
        if not memories:
            return ""
        texts = [m.content for m in memories if m.content.strip()]
        return self._summarizer.summarize(texts)

    def deduplicate(
        self,
        memories: List[MemoryEntry],
        threshold: float = 0.9,
    ) -> List[MemoryEntry]:
        """
        检测和合并重复记忆

        基于内容相似度（bigram Jaccard + 编辑距离）进行去重。
        对于相似度超过阈值的记忆对，保留重要性更高的那条。

        Args:
            memories: 记忆条目列表
            threshold: 相似度阈值（默认 0.9）

        Returns:
            去重后的记忆列表
        """
        return self._deduplicator.deduplicate(memories, threshold)

    def consolidate_short_to_long(
        self,
        short_term: ShortTermStore,
        long_term: LongTermStore,
    ) -> int:
        """
        整合短期记忆到长期记忆

        流程：
        1. 获取短期记忆中的所有条目
        2. 评估每条记忆的重要性
        3. 去除重复
        4. 将重要性达标（>= 0.4）的记忆写入长期存储
        5. 清空已被整合的短期记忆

        Args:
            short_term: 短期记忆存储
            long_term: 长期记忆存储

        Returns:
            成功整合到长期记忆的数量
        """
        short_memories = list(short_term.memories)
        if not short_memories:
            logger.debug("短期记忆为空，无需整合")
            return 0

        # 1. 去重
        unique_memories = self.deduplicate(short_memories, threshold=0.85)

        # 2. 评估重要性并筛选
        consolidated_count = 0
        importance_threshold = 0.4

        for mem in unique_memories:
            # 重新评估重要性（如果还没有评估过）
            if mem.importance < 0.01:
                mem.importance = self.score_importance(mem.content)

            # 重要性达标则写入长期记忆
            if mem.importance >= importance_threshold:
                long_term.store(
                    content=mem.content,
                    importance=mem.importance,
                    tags=mem.tags.copy() if mem.tags else set(),
                )
                consolidated_count += 1

        # 3. 清空短期记忆
        short_term.clear()

        logger.info(
            f"短期→长期整合完成: {len(short_memories)} 条短期记忆，"
            f"去重后 {len(unique_memories)} 条，"
            f"整合 {consolidated_count} 条到长期记忆"
        )
        return consolidated_count

    def compress_old_memories(
        self,
        memories: List[MemoryEntry],
        days: int = 7,
    ) -> List[MemoryEntry]:
        """
        压缩超过 N 天的旧记忆

        对超过指定天数的记忆：
        1. 先按时间分组（每天一组）
        2. 同一天的记忆生成一条摘要记忆
        3. 未超过天数的记忆保持原样

        Args:
            memories: 记忆条目列表
            days: 天数阈值（默认 7 天）

        Returns:
            压缩后的记忆列表（旧记忆被摘要替换）
        """
        if not memories:
            return []

        cutoff = datetime.now() - timedelta(days=days)

        old_memories: List[MemoryEntry] = []
        new_memories: List[MemoryEntry] = []

        for mem in memories:
            if mem.created_at < cutoff:
                old_memories.append(mem)
            else:
                new_memories.append(mem)

        if not old_memories:
            return memories  # 没有需要压缩的旧记忆

        # ---- 按日期分组 ----
        day_groups: Dict[str, List[MemoryEntry]] = {}
        for mem in old_memories:
            day_key = mem.created_at.strftime("%Y-%m-%d")
            day_groups.setdefault(day_key, []).append(mem)

        # ---- 每天生成一条摘要记忆 ----
        compressed: List[MemoryEntry] = []
        for day_key in sorted(day_groups.keys()):
            group = day_groups[day_key]
            if len(group) == 1:
                # 只有一条，直接保留
                compressed.append(group[0])
            else:
                # 多条：生成摘要
                summary_text = self.summarize(group)
                # 取组内最高重要性
                max_importance = max(m.importance for m in group)
                # 合并所有标签
                merged_tags: Set[str] = set()
                for m in group:
                    merged_tags.update(m.tags)

                summary_entry = MemoryEntry(
                    content=f"[{day_key} 摘要] {summary_text}",
                    importance=max_importance,
                    tags=merged_tags,
                    created_at=group[0].created_at,  # 保留最早的日期
                )
                compressed.append(summary_entry)
                logger.debug(
                    f"压缩 {day_key}: {len(group)} 条 → 1 条摘要"
                )

        result = new_memories + compressed
        logger.info(
            f"记忆压缩完成: {len(memories)} 条 → {len(result)} 条"
            f"（压缩了 {len(old_memories)} 条超过 {days} 天的旧记忆）"
        )
        return result
