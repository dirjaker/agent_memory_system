# Agent Memory System 项目方向指引

## 🎯 项目定位

Agent Memory System 是一个**智能体记忆系统**，目的是：
1. 理解 AI Agent 的记忆机制
2. 掌握六层记忆系统设计（认知科学驱动）
3. 学习混合检索技术（BM25 + 语义向量）
4. 掌握 Embedding 抽象层设计
5. 为面试提供可讲解的项目经验

---

## 📚 学习路径

### 阶段一：记忆基础（Week 1）
- [x] 理解记忆的分类（感觉/短期/工作/长期）
- [x] 实现基础的记忆存储
- [x] 实现记忆的增删改查

### 阶段二：记忆管理（Week 2）
- [x] 实现记忆管理器
- [x] 实现记忆流转机制
- [x] 实现遗忘机制（艾宾浩斯曲线）

### 阶段三：向量检索（Week 3）
- [x] 理解向量嵌入概念
- [x] 实现简单的向量存储
- [x] 实现相似度搜索

### 阶段四：高级功能（Week 4+）
- [x] Embedding 抽象层（多模型支持 + 自动降级）
- [x] 混合检索引擎（BM25 + 语义 + RRF 融合）
- [x] 记忆整合器（压缩/去重/重要性评估）
- [x] 情景记忆 + 语义记忆
- [x] SQLite 持久化
- [x] Web API + 桌面 GUI

### 阶段五：生产化（未来）
- [ ] 集成 ChromaDB / FAISS
- [ ] 多 Agent 记忆共享
- [ ] 记忆可视化仪表盘
- [ ] 单元测试覆盖

---

## 🎓 面试要点

### 核心概念
1. **六层记忆架构**：为什么需要多级记忆？每一层的设计依据？
2. **记忆流转**：短期记忆如何变成长期记忆？
3. **遗忘机制**：基于艾宾浩斯曲线的渐进衰减 vs 简单 TTL
4. **混合检索**：BM25 + 语义向量的融合策略
5. **Embedding 抽象**：策略模式 + 工厂模式 + 自动降级

### 常见问题

**Q: 为什么 Agent 需要记忆系统？**
> 没有记忆的 Agent 每次对话都是从零开始。记忆系统让 Agent 能够：
> - 保持对话连贯性
> - 学习用户偏好
> - 积累知识和经验

**Q: 六层记忆各有什么用途？**
> - 感觉记忆：缓存输入流，极短暂（环形缓冲区）
> - 短期记忆：当前对话上下文（重要性淘汰）
> - 工作记忆：当前任务相关信息（LRU 淘汰）
> - 长期记忆：持久化的知识和经验（三因子评分 + 自动遗忘）
> - 情景记忆：对话历史管理（按会话组织）
> - 语义记忆：事实知识图谱（三元组存储）

**Q: 如何实现记忆的遗忘？**
> 基于艾宾浩斯遗忘曲线：`score = importance × 2^(-t/T_half)`
> - 新记忆衰减快
> - 重要记忆衰减慢
> - 频繁访问的记忆更持久
> - 渐进衰减而非突然删除

**Q: 混合检索的原理是什么？**
> 1. BM25 检索：TF-IDF 变体，擅长精确匹配
> 2. 语义检索：Embedding 向量余弦相似度，擅长语义理解
> 3. RRF 融合：`score = Σ 1/(k + rank_i)`，综合两路排名
> 4. Reranker 重排序：二次排序提升最终质量

---

## 🔗 技术关联

### 与其他项目的关系

```
agent_memory_system
├── 被 agent_platform 使用（Agent 记忆）
├── 被 multi_agent_crew 使用（团队共享记忆）
├── 使用 knowledge_graph 的知识
└── 可被 agent_evaluator 评估
```

### 技术栈

- **核心**：Python 3.8+, dataclasses, abc
- **可选**：sentence-transformers, scikit-learn
- **Web**：FastAPI, Uvicorn, Pydantic
- **持久化**：SQLite（WAL 模式）

---

## 📖 参考资源

### 论文
- [Memory Networks](https://arxiv.org/abs/1410.3916)
- [End-To-End Memory Networks](https://arxiv.org/abs/1503.08895)
- [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)

### 开源项目
- [LangChain Memory](https://github.com/langchain-ai/langchain)
- [MemGPT](https://github.com/cpacker/MemGPT)
- [ChromaDB](https://github.com/chroma-core/chroma)

---

## ⚡ 快速命令

```bash
# 运行示例
python examples/memory_demo.py
python examples/enhanced_demo.py
python examples/vector_search.py

# 启动 Web API
python -m src.web.app

# 启动 macOS GUI
python -m src.macos.app

# 验证安装
python -c "from src import create_memory_manager; print('OK')"
```
