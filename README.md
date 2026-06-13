<div align="center">

# 🧠 Agent Memory System

### AI Agent 记忆管理系统 v2.0

[![版本](https://img.shields.io/badge/版本-2.0-blue?style=flat-square)]()
[![存储](https://img.shields.io/badge/存储-4-green?style=flat-square)]()
[![检索](https://img.shields.io/badge/检索-向量+FTS-orange?style=flat-square)]()
[![更新](https://img.shields.io/badge/更新-2025.06-red?style=flat-square)]()

*短期/长期/工作记忆 · 向量检索 · 记忆压缩 · 多存储后端*

</div>

---

> 智能体记忆系统 - 为 AI Agent 提供多层级记忆能力

## ✨ 特性

- 🧠 **六级记忆架构**：感觉 → 短期 → 工作 → 长期 → 情景 → 语义记忆
- 🔄 **记忆流转**：自动将重要记忆从短期转入长期
- 🔍 **混合检索**：BM25 关键词检索 + 语义向量检索 + 重排序
- ⏳ **遗忘机制**：基于艾宾浩斯曲线的记忆衰减
- 🗜️ **记忆整合**：LLM 驱动 / 规则降级的智能整合与压缩
- 💾 **SQLite 持久化**：轻量级本地数据库持久化
- 🧩 **Embedding 抽象层**：支持 Sentence-Transformers、OpenAI、TF-IDF、Hash
- 📖 **情景记忆**：对话历史管理（按会话组织）
- 🏷️ **语义记忆**：三元组事实知识图谱
- 📊 **可观测性**：运行时统计报告

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/dirjaker/agent_memory_system.git
cd agent_memory_system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装核心依赖（零依赖，开箱即用）
pip install -r requirements.txt

# 可选：安装语义嵌入支持
pip install sentence-transformers
# 可选：安装 TF-IDF 支持
pip install scikit-learn
# 可选：安装 OpenAI 嵌入
pip install openai
```

### 基础用法

```python
from src import create_memory_manager

# 创建记忆管理器
manager = create_memory_manager()

# 感知输入 -> 感觉记忆 + 短期记忆
manager.perceive("用户问：什么是 AI Agent？")

# 主动记忆 -> 工作记忆（高重要性同时存入长期记忆）
manager.remember("AI Agent 是自主执行任务的智能体", importance=0.8)

# 回忆检索
results = manager.recall("Agent")

# 获取上下文
context = manager.get_context()
```

### v2.0 新功能

```python
from src import create_memory_manager

manager = create_memory_manager()

# ---- 情景记忆：对话历史 ----
manager.add_episodic("conv_001", "user", "什么是 Transformer？")
manager.add_episodic("conv_001", "assistant", "Transformer 是一种基于自注意力机制的深度学习模型。")

# ---- 语义记忆：事实知识 ----
manager.add_semantic("Python 是一种编程语言", entities=["Python"])
manager.add_semantic("Transformer 由 Google 提出", entities=["Transformer"])

# ---- 自动整合 ----
count = manager.auto_consolidate()  # 短期 -> 长期
compressed = manager.compress_memory(days=7)  # 压缩旧记忆

# ---- 混合检索 ----
results = manager.search_memories("Python", limit=5)
for r in results:
    print(f"[{r.source}] (score={r.score:.2f}) {r.content}")

# ---- 为 LLM 生成上下文 ----
llm_context = manager.get_context_for_llm(query="Python", limit=5)
print(llm_context)

# ---- SQLite 持久化 ----
manager.save_to_db("my_memories.db")
manager.load_from_db("my_memories.db")

# ---- 可观测性 ----
report = manager.get_observability_report()
print(report)
```

## 📁 项目结构

```
agent_memory_system/
├── src/
│   ├── __init__.py              # 包初始化（导出所有公共类）
│   ├── memory_store.py          # 记忆存储实现（6 级记忆）
│   ├── memory_manager.py        # 记忆管理器（统一入口）
│   ├── vector_store.py          # 向量存储
│   ├── embedding.py             # Embedding 抽象层
│   ├── persistence.py           # SQLite 持久化层
│   ├── memory_consolidator.py   # 记忆整合器
│   └── retriever.py             # 混合检索器（BM25 + 语义）
├── examples/
│   ├── memory_demo.py           # 基础记忆演示
│   ├── vector_search.py         # 向量搜索演示
│   └── enhanced_demo.py         # v2.0 完整功能演示
├── TECHNICAL_DOC.md             # 技术文档
├── DIRECTION.md                 # 方向指引
├── VERSION.md                   # 版本记录
├── requirements.txt             # 依赖列表
└── README.md                    # 项目说明
```

## 🧠 记忆层级

```
输入
  ↓
┌─────────────────┐
│ Sensory Buffer  │ 感觉记忆（< 1秒）
└────────┬────────┘
         ↓
┌─────────────────┐
│ Short-term Store│ 短期记忆（几分钟）
└────────┬────────┘
         ↓
┌─────────────────┐
│ Working Memory  │ 工作记忆（当前任务）
└────────┬────────┘
         ↓
┌─────────────────┐
│ Long-term Store │ 长期记忆（持久）
└─────────────────┘
         ↓
┌──────────────────────┐   ┌──────────────────────┐
│ Episodic Memory      │   │ Semantic Memory      │
│ （情景：对话历史）    │   │ （语义：事实知识）    │
└──────────────────────┘   └──────────────────────┘
```

## 🔧 核心功能

### 1. 感知输入 (Perceive)

```python
manager.perceive("用户说了什么...")
```

自动存入感觉记忆和短期记忆。

### 2. 主动记忆 (Remember)

```python
manager.remember("重要信息", importance=0.9, tags={"AI", "重要"})
```

高重要性记忆自动转入长期记忆。

### 3. 回忆检索 (Recall)

```python
results = manager.recall("搜索关键词", limit=5)
```

跨层级搜索相关记忆。

### 4. 混合检索 (Search)

```python
results = manager.search_memories("查询", limit=5)
# 搜索所有层级（短期/工作/长期/情景/语义），按综合分数排序
```

### 5. 记忆整合 (Consolidate)

```python
manager.consolidate()       # 手动整合
manager.auto_consolidate()  # 自动整合（使用 Consolidator 评估重要性）
manager.compress_memory(days=7)  # 压缩旧记忆
```

### 6. 遗忘机制 (Forget)

```python
manager.forget(hours=24)
```

清理过期的记忆。

### 7. LLM 上下文生成

```python
context = manager.get_context_for_llm(query="相关查询", limit=10)
# 自动组合工作记忆 + 对话历史 + 事实知识 + 长期记忆
```

### 8. SQLite 持久化

```python
manager.save_to_db("memory.db")
manager.load_from_db("memory.db")
```

### 9. 可观测性

```python
report = manager.get_observability_report()
# 包含各层记忆统计、整合器状态、情景/语义记忆统计
```

## 📊 运行示例

```bash
# 基础记忆演示
python examples/memory_demo.py

# 向量搜索演示
python examples/vector_search.py

# v2.0 完整功能演示
python examples/enhanced_demo.py
```

## 🎯 应用场景

- 💬 **对话系统**：记住对话历史，保持连贯性
- 👤 **个性化 Agent**：记住用户偏好
- 📚 **知识库**：长期存储学习到的知识
- 🤖 **多轮对话**：跨会话的记忆保持
- 🧩 **RAG 系统**：为 LLM 提供结构化上下文

## 📚 文档

- [技术文档](TECHNICAL_DOC.md) - 架构设计、模块详解
- [方向指引](DIRECTION.md) - 项目规划、学习路径
- [版本记录](VERSION.md) - 更新日志

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License


---

## Web 界面

基于 FastAPI 的 REST API 与暗色主题仪表盘。

### 启动

```bash
python src/web/app.py
# 访问 http://localhost:8081
```

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/perceive` | POST | 感知输入 (感觉 + 短期记忆) |
| `/api/remember` | POST | 主动记忆 (工作记忆) |
| `/api/recall` | POST | 回忆检索 |
| `/api/search` | POST | 混合检索 (BM25 + 语义) |
| `/api/episodic` | POST | 添加情景记忆 |
| `/api/semantic` | POST | 添加语义记忆 |
| `/api/consolidate` | POST | 记忆整合 |
| `/api/compress` | POST | 压缩旧记忆 |
| `/api/context` | GET | 获取 LLM 上下文 |
| `/api/stats` | GET | 记忆统计 |
| `/api/save` | POST | 保存到 SQLite |
| `/api/load` | POST | 从 SQLite 加载 |

### 仪表盘

暗色主题仪表盘，支持:
- 记忆层统计面板 (感觉/短期/工作/长期/情景/语义)
- 感知输入与主动记忆
- 回忆检索与混合检索
- 情景记忆与语义知识管理
- 记忆整合与压缩操作
- LLM 上下文生成

---

## macOS 应用

### tkinter 桌面版

```bash
python src/macos/app.py
```

### py2app 打包

```bash
# 在 macOS 上执行
python packaging/py2app_setup.py py2app
# 产物位于 dist/Agent Memory System.app
```
