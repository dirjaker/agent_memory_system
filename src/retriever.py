"""
混合检索器模块
==============

提供多种检索策略，支持关键词检索、语义检索、混合检索和重排序。

组件:
- RetrievalResult: 检索结果数据类
- BM25Retriever: BM25 关键词检索（TF-IDF 变体）
- SemanticRetriever: 基于嵌入向量的语义检索
- HybridRetriever: 融合关键词和语义搜索的混合检索器
- Reranker: 基于查询相关性的结果重排序

作者：dirjaker
创建日期：2026-06-02
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import math
import re
import logging
from collections import Counter

from .embedding import BaseEmbedding
from .memory_store import MemoryEntry

logger = logging.getLogger(__name__)


# ============================================================
# 检索结果数据类
# ============================================================

@dataclass
class RetrievalResult:
    """
    检索结果

    统一的检索结果格式，无论来自哪种检索策略。

    Attributes:
        content: 检索到的文本内容
        score: 综合相关性分数（越高越相关）
        source: 来源标识，表示结果来自哪个记忆层
                （如 "long_term", "episodic", "semantic", "short_term" 等）
        metadata: 附加元数据（如创建时间、标签、重要性等）
    """
    content: str
    score: float
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "content": self.content,
            "score": round(self.score, 4),
            "source": self.source,
            "metadata": self.metadata,
        }


# ============================================================
# BM25 检索器
# ============================================================

class BM25Retriever:
    """
    BM25 关键词检索器

    实现 Okapi BM25 算法，是 TF-IDF 的改进变体。
    BM25 在信息检索领域被广泛使用，通过对词频进行饱和处理
    和文档长度归一化来提升检索质量。

    BM25 评分公式:
        score(Q, D) = Σ IDF(qi) · (f(qi, D) · (k1 + 1)) /
                       (f(qi, D) + k1 · (1 - b + b · |D| / avgdl))

    其中:
        - f(qi, D): 词 qi 在文档 D 中的词频
        - |D|: 文档 D 的长度
        - avgdl: 平均文档长度
        - k1: 词频饱和参数（越大则词频影响越大）
        - b: 文档长度归一化参数（0=不归一化，1=完全归一化）

    使用方式:
        >>> retriever = BM25Retriever()
        >>> retriever.fit(["文档1内容", "文档2内容", "文档3内容"])
        >>> results = retriever.search("查询关键词", top_k=3)
        >>> for idx, score in results:
        ...     print(f"文档{idx}: {score:.4f}")
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 检索器

        Args:
            k1: 词频饱和参数，控制词频对评分的影响程度。
                值越大，高频词的权重越高。典型范围 [1.2, 2.0]
            b: 文档长度归一化参数。
               b=0 不考虑文档长度差异，b=1 完全按长度归一化。
        """
        self.k1 = k1
        self.b = b

        # 内部状态
        self._documents: List[str] = []          # 原始文档列表
        self._tokenized_docs: List[List[str]] = []  # 分词后的文档
        self._doc_lengths: List[int] = []        # 每个文档的 token 数
        self._avg_doc_length: float = 0.0        # 平均文档长度
        self._idf: Dict[str, float] = {}         # 词 -> IDF 值
        self._fitted: bool = False               # 是否已建立索引

    def fit(self, documents: List[str]) -> None:
        """
        建立 BM25 索引

        对文档列表进行分词、统计词频和文档频率，
        预计算 IDF 值，为后续搜索做准备。

        Args:
            documents: 文档文本列表
        """
        self._documents = documents
        n = len(documents)

        if n == 0:
            self._fitted = True
            logger.warning("BM25Retriever.fit() 收到空文档列表")
            return

        # 对所有文档分词
        self._tokenized_docs = [self._tokenize(doc) for doc in documents]
        self._doc_lengths = [len(tokens) for tokens in self._tokenized_docs]
        self._avg_doc_length = sum(self._doc_lengths) / n

        # 统计每个词出现在多少个文档中（文档频率）
        doc_freq: Dict[str, int] = {}
        for tokens in self._tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # 计算 IDF 值
        # IDF 公式: log((N - n + 0.5) / (n + 0.5) + 1)
        self._idf = {}
        for token, freq in doc_freq.items():
            self._idf[token] = math.log((n - freq + 0.5) / (freq + 0.5) + 1)

        self._fitted = True
        logger.info(f"BM25 索引建立完成: {n} 篇文档, 词汇量 {len(self._idf)}")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        BM25 搜索

        对查询进行分词，计算每个文档的 BM25 评分，
        返回评分最高的 top_k 个结果。

        Args:
            query: 查询文本
            top_k: 返回结果数量，默认 5

        Returns:
            List[Tuple[int, float]]: (文档索引, BM25 分数) 的列表，
            按分数降序排列。文档索引对应 fit() 时传入的 documents 列表下标。
        """
        if not self._fitted:
            logger.warning("BM25 尚未建立索引，请先调用 fit()")
            return []

        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 计算每个文档的 BM25 分数
        scores: List[Tuple[int, float]] = []
        for i, doc_tokens in enumerate(self._tokenized_docs):
            score = self._compute_bm25_score(query_tokens, doc_tokens, i)
            if score > 0:
                scores.append((i, score))

        # 按分数降序排序，返回 top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _compute_bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_idx: int,
    ) -> float:
        """
        计算单个文档的 BM25 评分

        Args:
            query_tokens: 查询的 token 列表
            doc_tokens: 文档的 token 列表
            doc_idx: 文档索引（用于获取文档长度）

        Returns:
            float: BM25 分数
        """
        doc_len = self._doc_lengths[doc_idx]
        tf_counter = Counter(doc_tokens)

        score = 0.0
        for token in query_tokens:
            if token not in tf_counter:
                continue

            tf = tf_counter[token]
            idf = self._idf.get(token, 0.0)

            # BM25 核心公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_length)
            score += idf * numerator / denominator

        return score

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        中英文分词

        简单的分词策略:
        - 英文: 按空格和标点分词，转小写
        - 中文: 每个字符作为一个 token，同时生成 bigram

        Args:
            text: 输入文本

        Returns:
            List[str]: token 列表
        """
        text = text.lower()
        tokens: List[str] = []

        # 提取英文单词
        english_words = re.findall(r'[a-z]+', text)
        tokens.extend(english_words)

        # 提取中文字符（每个字作为一个 token）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(chinese_chars)

        # 中文 bigram（相邻两个字的组合，捕获短语信息）
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i + 1])

        return tokens


# ============================================================
# 语义检索器
# ============================================================

class SemanticRetriever:
    """
    语义检索器

    使用嵌入向量进行语义相似度搜索。
    通过将查询和文档都转换为向量，计算余弦相似度来衡量语义相关性。

    与关键词检索不同，语义检索能够理解同义词、近义表达，
    即使查询和文档没有共同的关键词也能匹配。

    使用方式:
        >>> from .embedding import SentenceTransformerEmbedding
        >>> embedding = SentenceTransformerEmbedding()
        >>> retriever = SemanticRetriever(embedding=embedding)
        >>> results = retriever.search("查询文本", memories, top_k=5)
    """

    def __init__(self, embedding: BaseEmbedding):
        """
        初始化语义检索器

        Args:
            embedding: 嵌入模型实例，用于将文本转换为向量
        """
        self._embedding = embedding

    def search(
        self,
        query: str,
        documents: List[MemoryEntry],
        top_k: int = 5,
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        语义搜索

        将查询文本嵌入为向量，与每个文档的嵌入向量计算余弦相似度，
        返回最相关的 top_k 个结果。

        Args:
            query: 查询文本
            documents: 记忆条目列表，每个条目应已有 embedding 字段
            top_k: 返回结果数量，默认 5

        Returns:
            List[Tuple[MemoryEntry, float]]: (记忆条目, 余弦相似度) 的列表，
            按相似度降序排列。
        """
        if not documents:
            return []

        # 将查询文本转换为向量
        query_vec = self._embedding.embed_text(query)

        # 过滤掉没有 embedding 的条目
        valid_docs = [doc for doc in documents if doc.embedding]
        if not valid_docs:
            logger.warning("SemanticRetriever: 所有文档均缺少 embedding")
            return []

        # 计算余弦相似度
        scored: List[Tuple[MemoryEntry, float]] = []
        for doc in valid_docs:
            sim = self._cosine_similarity(query_vec, doc.embedding)
            scored.append((doc, sim))

        # 按相似度降序排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度

        cosine_sim(A, B) = (A · B) / (||A|| * ||B||)

        Args:
            vec1: 向量 A
            vec2: 向量 B

        Returns:
            float: 余弦相似度，范围 [-1, 1]
        """
        if len(vec1) != len(vec2):
            logger.warning(
                f"向量维度不匹配: {len(vec1)} vs {len(vec2)}，返回 0"
            )
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# ============================================================
# 混合检索器
# ============================================================

class HybridRetriever:
    """
    混合检索器

    融合 BM25 关键词检索和语义向量检索的结果，
    综合两者的优势以获得更好的检索效果。

    融合策略:
        final_score = keyword_weight * bm25_score + semantic_weight * semantic_score

    支持降级模式: 当没有嵌入模型时，自动退化为纯关键词检索。

    使用方式:
        >>> from .embedding import SentenceTransformerEmbedding
        >>> embedding = SentenceTransformerEmbedding()
        >>> retriever = HybridRetriever(embedding=embedding)
        >>> results = retriever.search("查询文本", memories_dict, top_k=5)
    """

    def __init__(
        self,
        embedding: Optional[BaseEmbedding] = None,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
    ):
        """
        初始化混合检索器

        Args:
            embedding: 嵌入模型实例。为 None 时进入降级模式（仅关键词检索）
            keyword_weight: 关键词检索权重，范围 [0, 1]
            semantic_weight: 语义检索权重，范围 [0, 1]
        """
        self._embedding = embedding
        self._keyword_weight = keyword_weight
        self._semantic_weight = semantic_weight

        # 初始化子检索器
        self._bm25 = BM25Retriever()
        self._semantic: Optional[SemanticRetriever] = None

        if embedding is not None:
            self._semantic = SemanticRetriever(embedding=embedding)
        else:
            logger.warning(
                "HybridRetriever: 未提供 embedding，进入降级模式（仅关键词检索）"
            )

    def search(
        self,
        query: str,
        memories: Dict[str, List[MemoryEntry]],
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        混合搜索

        从多个记忆层中检索相关结果，融合关键词和语义搜索的分数。

        步骤:
        1. 将所有记忆层的条目汇总，建立 BM25 索引
        2. BM25 关键词检索，获取初始结果
        3. 语义向量检索（如果可用），获取初始结果
        4. 融合两组分数（加权求和）
        5. 返回 top_k 个最终结果

        Args:
            query: 查询文本
            memories: 记忆字典，key 为记忆层名称（如 "long_term"），
                     value 为该层的记忆条目列表
            top_k: 返回结果数量，默认 5

        Returns:
            List[RetrievalResult]: 融合后的检索结果列表，按综合分数降序排列
        """
        if not memories:
            return []

        # ---- 1. 汇总所有记忆条目，记录来源 ----
        all_entries: List[MemoryEntry] = []     # 所有条目（保持顺序）
        entry_source: Dict[int, str] = {}       # 条目 id -> 来源层名称
        entry_texts: List[str] = []             # 用于 BM25 的文本列表

        for source_name, entries in memories.items():
            for entry in entries:
                entry_source[id(entry)] = source_name
                all_entries.append(entry)
                entry_texts.append(entry.content)

        if not all_entries:
            return []

        # ---- 2. BM25 关键词检索 ----
        self._bm25.fit(entry_texts)
        bm25_results = self._bm25.search(query, top_k=top_k * 3)

        # 将 BM25 结果映射为 {条目: 分数}
        bm25_scores: Dict[int, float] = {}  # id(entry) -> score
        for idx, score in bm25_results:
            bm25_scores[id(all_entries[idx])] = score

        # ---- 3. 语义检索（如果可用）----
        semantic_scores: Dict[int, float] = {}  # id(entry) -> score

        if self._semantic is not None:
            # 只对有 embedding 的条目做语义检索
            entries_with_embedding = [e for e in all_entries if e.embedding]
            if entries_with_embedding:
                sem_results = self._semantic.search(
                    query, entries_with_embedding, top_k=top_k * 3
                )
                for entry, score in sem_results:
                    semantic_scores[id(entry)] = score

        # ---- 4. 融合分数 ----
        # 归一化 BM25 分数到 [0, 1]
        bm25_max = max(bm25_scores.values()) if bm25_scores else 1.0
        # 归一化语义分数到 [0, 1]
        sem_max = max(semantic_scores.values()) if semantic_scores else 1.0

        # 收集所有出现在结果中的条目 ID
        candidate_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())

        fused: List[RetrievalResult] = []
        for entry in all_entries:
            eid = id(entry)
            if eid not in candidate_ids:
                continue

            # 归一化后的分数
            kw_score = (bm25_scores.get(eid, 0) / bm25_max) if bm25_max > 0 else 0
            sem_score = (semantic_scores.get(eid, 0) / sem_max) if sem_max > 0 else 0

            # 如果没有语义模型，关键词权重提升为 1.0
            if self._semantic is None:
                final_score = kw_score  # 降级：纯关键词
            else:
                final_score = (
                    self._keyword_weight * kw_score
                    + self._semantic_weight * sem_score
                )

            source_name = entry_source.get(eid, "unknown")
            metadata = dict(entry.metadata) if entry.metadata else {}
            metadata["entry_id"] = entry.id
            metadata["importance"] = entry.importance
            metadata["access_count"] = entry.access_count

            fused.append(RetrievalResult(
                content=entry.content,
                score=final_score,
                source=source_name,
                metadata=metadata,
            ))

        # 按综合分数降序排序
        fused.sort(key=lambda r: r.score, reverse=True)
        return fused[:top_k]


# ============================================================
# 重排序器
# ============================================================

class Reranker:
    """
    重排序器

    对初步检索结果进行二次排序，以提升最终结果的相关性。

    原理:
        使用嵌入模型计算查询与每个结果的语义相似度，
        将该相似度与原始分数加权融合，得到更准确的排序。

    使用方式:
        >>> reranker = Reranker(embedding=embedding_model)
        >>> reranked = reranker.rerank("查询文本", retrieval_results, top_k=5)
    """

    def __init__(self, embedding: Optional[BaseEmbedding] = None):
        """
        初始化重排序器

        Args:
            embedding: 嵌入模型实例。为 None 时仅基于原始分数排序（不重排）
        """
        self._embedding = embedding

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        对检索结果重排序

        使用嵌入模型计算查询与每个结果的语义相似度，
        将相似度与原始分数融合后重新排序。

        融合公式:
            new_score = 0.4 * original_score + 0.6 * semantic_similarity

        Args:
            query: 查询文本
            results: 待重排序的检索结果列表
            top_k: 返回结果数量，默认 5

        Returns:
            List[RetrievalResult]: 重排序后的结果列表
        """
        if not results:
            return []

        # 无嵌入模型时，仅按原始分数排序
        if self._embedding is None:
            logger.debug("Reranker: 无嵌入模型，仅按原始分数排序")
            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]

        # 将查询文本嵌入为向量
        query_vec = self._embedding.embed_text(query)

        # 计算每个结果与查询的语义相似度
        reranked: List[RetrievalResult] = []
        for result in results:
            result_vec = self._embedding.embed_text(result.content)
            semantic_sim = SemanticRetriever._cosine_similarity(query_vec, result_vec)

            # 融合原始分数和语义相似度
            # 原始分数权重 0.4，语义相似度权重 0.6
            new_score = 0.4 * result.score + 0.6 * semantic_sim

            # 创建新的 RetrievalResult（保留原始 metadata）
            reranked.append(RetrievalResult(
                content=result.content,
                score=new_score,
                source=result.source,
                metadata=dict(result.metadata),
            ))

        # 按融合后的分数降序排序
        reranked.sort(key=lambda r: r.score, reverse=True)
        return reranked[:top_k]
