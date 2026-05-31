# Agent Memory System 版本记录

## v1.0.0 (2026-05-30)

### 🎉 初始版本

#### 核心功能
- **Memory Store 模块**
  - MemoryEntry 记忆条目
  - SensoryBuffer 感觉记忆
  - ShortTermStore 短期记忆
  - WorkingMemory 工作记忆
  - LongTermStore 长期记忆

- **Memory Manager 模块**
  - perceive() 感知输入
  - remember() 主动记忆
  - recall() 回忆检索
  - get_context() 获取上下文
  - consolidate() 记忆整合
  - forget() 遗忘机制

- **Vector Store 模块**
  - SimpleVectorStore 向量存储
  - 余弦相似度计算
  - 文本向量搜索

#### 示例代码
- `examples/memory_demo.py` - 记忆系统演示
- `examples/vector_search.py` - 向量搜索演示

#### 文档
- `README.md` - 项目说明
- `TECHNICAL_DOC.md` - 技术文档
- `DIRECTION.md` - 方向指引

---

## 后续计划

### v1.1.0 (计划中)
- [ ] 集成 Sentence Transformers
- [ ] 实现真实的向量嵌入
- [ ] 添加 FAISS 支持

### v1.2.0 (计划中)
- [ ] SQLite 持久化存储
- [ ] 多用户记忆隔离
- [ ] 记忆导出/导入

### v2.0.0 (远期)
- [ ] ChromaDB 集成
- [ ] 多模态记忆（图像、音频）
- [ ] 记忆共享机制
- [ ] Web UI
