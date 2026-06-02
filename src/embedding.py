"""
嵌入模型模块

提供多种嵌入(Embedding)实现方案，用于将文本转换为向量表示。
支持从高性能的 SentenceTransformer 到最简单的哈希降级方案，
以适应不同的运行环境和需求。

使用方式:
    # 工厂函数创建（推荐）
    embedder = create_embedding("sentence_transformer")
    vector = embedder.embed_text("你好世界")
    vectors = embedder.embed_batch(["文本1", "文本2"])

    # 直接实例化
    embedder = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")
    vector = embedder.embed_text("你好世界")
"""

from abc import ABC, abstractmethod
import hashlib
import math
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class BaseEmbedding(ABC):
    """
    嵌入模型抽象基类

    所有嵌入实现的接口定义。定义了文本嵌入的核心方法，
    包括单文本嵌入和批量嵌入。

    子类必须实现:
        - embed_text(): 将单条文本转换为向量
        - embed_batch(): 将多条文本批量转换为向量
        - dimension 属性: 返回向量维度

    示例:
        >>> class MyEmbedding(BaseEmbedding):
        ...     @property
        ...     def dimension(self) -> int:
        ...         return 128
        ...     def embed_text(self, text: str) -> List[float]:
        ...         return [0.0] * self.dimension
        ...     def embed_batch(self, texts: List[str]) -> List[List[float]]:
        ...         return [self.embed_text(t) for t in texts]
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        返回嵌入向量的维度

        Returns:
            int: 向量维度大小
        """
        ...

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        将单条文本转换为向量表示

        Args:
            text: 需要嵌入的文本字符串

        Returns:
            List[float]: 文本的向量表示，长度为 self.dimension

        Raises:
            RuntimeError: 嵌入过程中发生错误
        """
        ...

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        将多条文本批量转换为向量表示

        默认实现为逐条调用 embed_text，子类可覆盖以提供更高效的批量处理。

        Args:
            texts: 需要嵌入的文本列表

        Returns:
            List[List[float]]: 向量列表，与输入文本一一对应

        Raises:
            RuntimeError: 嵌入过程中发生错误
        """
        ...


class SentenceTransformerEmbedding(BaseEmbedding):
    """
    基于 SentenceTransformer 的嵌入模型

    使用 sentence-transformers 库加载预训练模型进行文本嵌入。
    默认使用 all-MiniLM-L6-v2 模型，兼顾速度和质量。

    特点:
        - 语义理解能力强，嵌入质量高
        - 支持 GPU 和 CPU 推理
        - 支持自定义模型名称

    依赖:
        pip install sentence-transformers

    示例:
        >>> embedder = SentenceTransformerEmbedding()
        >>> vector = embedder.embed_text("人工智能改变了世界")
        >>> print(len(vector))  # 384 (all-MiniLM-L6-v2 的维度)

        >>> # 使用 GPU
        >>> embedder = SentenceTransformerEmbedding(device="cuda")
    """

    # 常用模型及其维度映射
    MODEL_DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "all-MiniLM-L12-v2": 384,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "text2vec-base-chinese": 768,
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
    ):
        """
        初始化 SentenceTransformer 嵌入模型

        Args:
            model_name: 模型名称，支持 HuggingFace 上的所有 sentence-transformer 模型
            device: 运行设备，可选 'cuda'、'cpu' 或 None（自动检测）
            normalize_embeddings: 是否对嵌入向量做 L2 归一化，默认 True
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers 未安装。请运行: pip install sentence-transformers"
            )

        self._model_name = model_name
        self._normalize = normalize_embeddings

        logger.info(f"加载 SentenceTransformer 模型: {model_name} (device={device})")
        self._model = SentenceTransformer(model_name, device=device)
        fallback_dim = self._model.get_sentence_embedding_dimension()
        self._dim = self.MODEL_DIMENSIONS.get(model_name, fallback_dim or 384)
        logger.info(f"模型加载完成，向量维度: {self._dim}")

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        """
        将单条文本转换为向量

        Args:
            text: 输入文本

        Returns:
            List[float]: 文本的向量表示
        """
        embedding = self._model.encode(
            text, normalize_embeddings=self._normalize
        )
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量

        利用 SentenceTransformer 的批量处理能力，比逐条调用更高效。

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        if not texts:
            return []

        embeddings = self._model.encode(
            texts, normalize_embeddings=self._normalize, show_progress_bar=False
        )
        return [vec.tolist() for vec in embeddings]


class OpenAIEmbedding(BaseEmbedding):
    """
    基于 OpenAI API 的嵌入模型

    通过 OpenAI 的 Embedding API 获取高质量的文本嵌入向量。
    支持自定义 base_url 以兼容其他 OpenAI 兼容的 API 服务。

    特点:
        - 嵌入质量最高
        - 无需本地 GPU 资源
        - 需要 API Key 和网络连接
        - 会产生 API 调用费用

    依赖:
        pip install openai

    示例:
        >>> embedder = OpenAIEmbedding(api_key="sk-xxx")
        >>> vector = embedder.embed_text("Hello world")

        >>> # 使用自定义 API 端点
        >>> embedder = OpenAIEmbedding(
        ...     api_key="sk-xxx",
        ...     base_url="https://api.example.com/v1"
        ... )
    """

    # 模型维度映射
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        base_url: Optional[str] = None,
        max_batch_size: int = 2048,
    ):
        """
        初始化 OpenAI 嵌入模型

        Args:
            api_key: OpenAI API Key，如不提供则从环境变量 OPENAI_API_KEY 读取
            model: 嵌入模型名称，默认 text-embedding-3-small
            base_url: API 基础 URL，用于兼容其他 OpenAI 兼容服务
            max_batch_size: 单次 API 调用最大文本数量
        """
        try:
            import openai
        except ImportError:
            raise ImportError("openai 未安装。请运行: pip install openai")

        self._model = model
        self._max_batch_size = max_batch_size
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._dim = self.MODEL_DIMENSIONS.get(model, 1536)

        logger.info(f"初始化 OpenAI 嵌入模型: {model}")

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        """
        将单条文本通过 OpenAI API 转换为向量

        Args:
            text: 输入文本

        Returns:
            List[float]: 文本的向量表示

        Raises:
            openai.APIError: API 调用失败
        """
        response = self._client.embeddings.create(
            input=text, model=self._model
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量通过 OpenAI API 将文本转换为向量

        自动处理大批量文本的分片请求。

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        # 分批请求，避免超出 API 单次请求限制
        for i in range(0, len(texts), self._max_batch_size):
            batch = texts[i : i + self._max_batch_size]
            response = self._client.embeddings.create(
                input=batch, model=self._model
            )
            # 按 index 排序以保证顺序一致
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([item.embedding for item in sorted_data])

        return all_embeddings


class TFIDFEmbedding(BaseEmbedding):
    """
    基于 TF-IDF 的本地嵌入模型

    使用 scikit-learn 的 TfidfVectorizer 实现文本向量化。
    适用于无 GPU 环境、需要本地运行的场景。

    特点:
        - 纯本地运行，无需网络和 GPU
        - 依赖轻量（scikit-learn）
        - 语义理解能力有限（基于词频统计）
        - 需要先 fit 再 embed，以建立词汇表

    依赖:
        pip install scikit-learn

    示例:
        >>> embedder = TFIDFEmbedding()
        >>> corpus = ["我喜欢机器学习", "深度学习很有趣", "自然语言处理是AI的子领域"]
        >>> embedder.fit(corpus)
        >>> vector = embedder.embed_text("我喜欢AI")
        >>> vectors = embedder.embed_batch(corpus)
    """

    def __init__(
        self,
        max_features: int = 384,
        ngram_range: tuple = (1, 2),
        **tfidf_kwargs,
    ):
        """
        初始化 TF-IDF 嵌入模型

        Args:
            max_features: 最大特征数量（即向量维度上限），默认 384
            ngram_range: N-gram 范围，默认 (1, 2) 表示 unigram + bigram
            **tfidf_kwargs: 传递给 TfidfVectorizer 的其他参数
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            raise ImportError(
                "scikit-learn 未安装。请运行: pip install scikit-learn"
            )

        self._max_features = max_features
        self._vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            **tfidf_kwargs,
        )
        self._fitted = False
        self._dim = max_features

        logger.info(
            f"初始化 TF-IDF 嵌入模型 (max_features={max_features}, ngram_range={ngram_range})"
        )

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dim

    def fit(self, corpus: List[str]) -> "TFIDFEmbedding":
        """
        使用语料库训练 TF-IDF 模型

        必须在 embed_text / embed_batch 之前调用，用于构建词汇表。

        Args:
            corpus: 训练语料库（文本列表）

        Returns:
            TFIDFEmbedding: 返回自身，支持链式调用
        """
        self._vectorizer.fit(corpus)
        self._fitted = True
        vocab_size = len(self._vectorizer.vocabulary_)
        self._dim = vocab_size if vocab_size < self._max_features else self._max_features
        logger.info(f"TF-IDF 模型训练完成，词汇量: {vocab_size}，向量维度: {self._dim}")
        return self

    def embed_text(self, text: str) -> List[float]:
        """
        将单条文本转换为 TF-IDF 向量

        注意: 调用前必须先调用 fit() 方法。

        Args:
            text: 输入文本

        Returns:
            List[float]: TF-IDF 向量表示

        Raises:
            RuntimeError: 模型尚未 fit
        """
        if not self._fitted:
            raise RuntimeError(
                "TF-IDF 模型尚未训练。请先调用 fit(corpus) 方法。"
            )

        sparse_vector = self._vectorizer.transform([text])
        dense_vector = sparse_vector.toarray()[0]
        return dense_vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为 TF-IDF 向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表

        Raises:
            RuntimeError: 模型尚未 fit
        """
        if not texts:
            return []

        if not self._fitted:
            raise RuntimeError(
                "TF-IDF 模型尚未训练。请先调用 fit(corpus) 方法。"
            )

        sparse_matrix = self._vectorizer.transform(texts)
        dense_matrix = sparse_matrix.toarray()
        return [vec.tolist() for vec in dense_matrix]


class HashEmbedding(BaseEmbedding):
    """
    基于哈希的嵌入模型（降级方案）

    最简单的嵌入实现，使用文本哈希生成确定性向量。
    不依赖任何外部库，适合作为最后的降级兜底方案。

    特点:
        - 零依赖，任何 Python 环境均可运行
        - 确定性输出：相同输入总是产生相同向量
        - 语义理解能力最弱（无语义信息）
        - 速度快，适合对质量要求不高的场景

    原理:
        将文本哈希值拆分为多个字节，通过数学变换映射到 [-1, 1] 区间，
        再进行 L2 归一化，生成单位向量。

    示例:
        >>> embedder = HashEmbedding(dimension=384)
        >>> vector = embedder.embed_text("Hello world")
        >>> print(len(vector))  # 384
        >>> print(embedder.embed_text("Hello world") == embedder.embed_text("Hello world"))  # True
    """

    def __init__(self, dimension: int = 384):
        """
        初始化哈希嵌入模型

        Args:
            dimension: 输出向量的维度，默认 384
        """
        self._dim = dimension
        logger.info(f"初始化 Hash 嵌入模型 (dimension={dimension})")

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        """
        通过文本哈希生成确定性向量

        使用 SHA-512 哈希算法，循环填充至指定维度。
        对输出向量进行 L2 归一化以保证一致性。

        Args:
            text: 输入文本

        Returns:
            List[float]: 确定性的向量表示，长度为 self.dimension
        """
        # 使用 SHA-512 产生足够的哈希字节
        hash_bytes = hashlib.sha512(text.encode("utf-8")).digest()  # 64 bytes

        # 循环填充到目标维度
        raw_values = []
        for i in range(self._dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            # 映射到 [-1, 1] 区间
            normalized = (byte_val / 127.5) - 1.0
            raw_values.append(normalized)

        # L2 归一化
        norm = math.sqrt(sum(v * v for v in raw_values))
        if norm > 0:
            raw_values = [v / norm for v in raw_values]

        return raw_values

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量通过哈希生成确定性向量

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        return [self.embed_text(text) for text in texts]


def create_embedding(provider: str, **kwargs) -> BaseEmbedding:
    """
    嵌入模型工厂函数

    根据 provider 名称创建对应的嵌入模型实例。
    简化嵌入模型的初始化过程，方便统一管理。

    Args:
        provider: 嵌入模型提供者名称，支持以下值:
            - 'sentence_transformer': SentenceTransformer 模型（推荐，质量最佳本地方案）
            - 'openai': OpenAI Embedding API（需要 API Key）
            - 'tfidf': TF-IDF 模型（无 GPU 可用）
            - 'hash': 哈希模型（最后的降级方案）
        **kwargs: 传递给具体嵌入类构造函数的参数

    Returns:
        BaseEmbedding: 对应的嵌入模型实例

    Raises:
        ValueError: 不支持的 provider 名称

    示例:
        >>> # 使用 SentenceTransformer
        >>> embedder = create_embedding("sentence_transformer")
        >>> embedder = create_embedding("sentence_transformer", model_name="all-mpnet-base-v2")

        >>> # 使用 OpenAI
        >>> embedder = create_embedding("openai", api_key="sk-xxx")

        >>> # 使用 TF-IDF
        >>> embedder = create_embedding("tfidf", max_features=512)

        >>> # 使用哈希降级方案
        >>> embedder = create_embedding("hash", dimension=384)
    """
    providers = {
        "sentence_transformer": SentenceTransformerEmbedding,
        "openai": OpenAIEmbedding,
        "tfidf": TFIDFEmbedding,
        "hash": HashEmbedding,
    }

    provider_lower = provider.lower().strip()

    if provider_lower not in providers:
        supported = ", ".join(f"'{k}'" for k in providers.keys())
        raise ValueError(
            f"不支持的嵌入模型提供者: '{provider}'。"
            f"可选值: {supported}"
        )

    embedding_class = providers[provider_lower]
    logger.info(f"创建嵌入模型: {provider_lower} ({embedding_class.__name__})")

    try:
        return embedding_class(**kwargs)
    except Exception as e:
        logger.error(f"创建嵌入模型 '{provider}' 失败: {e}")
        raise
