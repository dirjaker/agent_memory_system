"""
Vector Store 向量存储模块
========================

实现基于向量的记忆检索：
- 简单的向量相似度计算
- 无需外部依赖的向量搜索
- 支持余弦相似度和欧氏距离
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import math
import random


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SimpleVectorStore:
    """
    简单的向量存储

    使用内存存储，支持基础的向量搜索
    实际项目中应替换为 FAISS、ChromaDB 等
    """

    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.documents: Dict[str, VectorDocument] = {}

    def add(
        self,
        doc_id: str,
        content: str,
        embedding: List[float] = None,
        metadata: Dict[str, Any] = None
    ) -> VectorDocument:
        """
        添加文档

        Args:
            doc_id: 文档 ID
            content: 文档内容
            embedding: 向量嵌入（如果不提供，会随机生成）
            metadata: 元数据

        Returns:
            VectorDocument
        """
        if embedding is None:
            embedding = self._simple_embed(content)

        doc = VectorDocument(
            id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        self.documents[doc_id] = doc
        return doc

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metric: str = "cosine"
    ) -> List[Tuple[VectorDocument, float]]:
        """
        向量搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            metric: 距离度量（cosine 或 euclidean）

        Returns:
            (文档, 相似度分数) 列表
        """
        if not self.documents:
            return []

        results = []
        for doc in self.documents.values():
            if metric == "cosine":
                score = self._cosine_similarity(query_embedding, doc.embedding)
            else:
                score = -self._euclidean_distance(query_embedding, doc.embedding)

            results.append((doc, score))

        # 按分数降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def search_by_text(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[VectorDocument, float]]:
        """
        文本搜索（先转为向量再搜索）

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            (文档, 相似度分数) 列表
        """
        query_embedding = self._simple_embed(query)
        return self.search(query_embedding, top_k)

    def delete(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def clear(self):
        """清空所有文档"""
        self.documents.clear()

    def _simple_embed(self, text: str) -> List[float]:
        """
        简单的文本嵌入

        注意：这是一个极简的嵌入方法，仅用于演示
        实际项目应使用：
        - OpenAI Embeddings
        - Sentence Transformers
        - Cohere Embed
        """
        # 使用文本哈希生成确定性的伪向量
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # 将哈希转换为浮点数向量
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                val = (hash_bytes[i] * 256 + hash_bytes[i + 1]) / 65535.0
            else:
                val = hash_bytes[i] / 255.0
            embedding.append(val)

        # 扩展到目标维度
        while len(embedding) < self.dimension:
            embedding.extend(embedding[:min(len(embedding), self.dimension - len(embedding))])

        return embedding[:self.dimension]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算欧氏距离"""
        if len(vec1) != len(vec2):
            return float('inf')

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "document_count": len(self.documents),
            "dimension": self.dimension
        }


def create_vector_store(dimension: int = 128) -> SimpleVectorStore:
    """
    创建向量存储的工厂函数

    Args:
        dimension: 向量维度

    Returns:
        SimpleVectorStore 实例
    """
    return SimpleVectorStore(dimension=dimension)
