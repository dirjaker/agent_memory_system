# Agent Memory System 项目方向指引

## 🎯 项目定位

Agent Memory System 是一个**智能体记忆学习项目**，目的是：
1. 理解 AI Agent 的记忆机制
2. 掌握多层级记忆系统设计
3. 学习向量检索技术
4. 为面试提供可讲解的项目经验

---

## 📚 学习路径

### 阶段一：记忆基础（Week 1）
- [x] 理解记忆的分类（感觉/短期/工作/长期）
- [x] 实现基础的记忆存储
- [x] 实现记忆的增删改查

### 阶段二：记忆管理（Week 2）
- [x] 实现记忆管理器
- [x] 实现记忆流转机制
- [x] 实现遗忘机制

### 阶段三：向量检索（Week 3）
- [x] 理解向量嵌入概念
- [x] 实现简单的向量存储
- [x] 实现相似度搜索

### 阶段四：真实集成（Week 4+）
- [ ] 集成 Sentence Transformers
- [ ] 集成 FAISS/ChromaDB
- [ ] 添加持久化存储

---

## 🎓 面试要点

### 核心概念
1. **记忆层级**：为什么需要多级记忆？
2. **记忆流转**：短期记忆如何变成长期记忆？
3. **遗忘机制**：如何决定哪些记忆该保留？
4. **向量检索**：如何实现语义搜索？

### 常见问题

**Q: 为什么 Agent 需要记忆系统？**
> 没有记忆的 Agent 每次对话都是从零开始。记忆系统让 Agent 能够：
> - 保持对话连贯性
> - 学习用户偏好
> - 积累知识和经验

**Q: 四级记忆各有什么用途？**
> - 感觉记忆：缓存输入，极短暂
> - 短期记忆：当前对话上下文
> - 工作记忆：当前任务相关信息
> - 长期记忆：持久化的知识和经验

**Q: 如何实现记忆的遗忘？**
> 基于艾宾浩斯遗忘曲线：
> - 新记忆衰减快
> - 重要记忆衰减慢
> - 频繁访问的记忆更持久
> - 定期清理低价值记忆

**Q: 向量搜索的原理是什么？**
> 1. 将文本转为向量（Embedding）
> 2. 计算向量间的相似度（余弦相似度）
> 3. 返回最相似的结果

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

- **核心**：Python 3.8+, dataclasses
- **可选**：sentence-transformers, faiss, chromadb
- **持久化**：SQLite, Redis

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

### 博客/教程
- 向量数据库入门
- RAG 系统设计
- Agent 记忆机制

---

## ⚡ 快速命令

```bash
# 运行示例
python examples/memory_demo.py
python examples/vector_search.py

# 测试代码
python -c "from src.memory_manager import create_memory_manager; print('OK')"
```
