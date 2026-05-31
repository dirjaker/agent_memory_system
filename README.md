# 🧠 Agent Memory System

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 智能体记忆系统 - 为 AI Agent 提供多层级记忆能力

## ✨ 特性

- 🧠 **四级记忆架构**：感觉记忆 → 短期记忆 → 工作记忆 → 长期记忆
- 🔄 **记忆流转**：自动将重要记忆从短期转入长期
- 🔍 **向量检索**：支持基于语义的相似度搜索
- ⏳ **遗忘机制**：基于艾宾浩斯曲线的记忆衰减

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/dirjaker/agent_memory_system.git
cd agent_memory_system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 基础用法

```python
from src.memory_manager import create_memory_manager

# 创建记忆管理器
manager = create_memory_manager()

# 感知输入
manager.perceive("用户问：什么是 AI Agent？")

# 主动记忆
manager.remember("AI Agent 是自主执行任务的智能体", importance=0.8)

# 回忆
results = manager.recall("Agent")

# 获取上下文
context = manager.get_context()
```

## 📁 项目结构

```
agent_memory_system/
├── src/
│   ├── __init__.py         # 包初始化
│   ├── memory_store.py     # 记忆存储实现
│   ├── memory_manager.py   # 记忆管理器
│   └── vector_store.py     # 向量存储
├── examples/
│   ├── memory_demo.py      # 记忆演示
│   └── vector_search.py    # 向量搜索演示
├── TECHNICAL_DOC.md        # 技术文档
├── DIRECTION.md            # 方向指引
├── VERSION.md              # 版本记录
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
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

### 4. 记忆整合 (Consolidate)

```python
manager.consolidate()
```

将重要的短期记忆转入长期记忆。

### 5. 遗忘机制 (Forget)

```python
manager.forget(hours=24)
```

清理过期的记忆。

## 📊 运行示例

```bash
# 记忆演示
python examples/memory_demo.py

# 向量搜索演示
python examples/vector_search.py
```

## 🎯 应用场景

- 💬 **对话系统**：记住对话历史，保持连贯性
- 👤 **个性化 Agent**：记住用户偏好
- 📚 **知识库**：长期存储学习到的知识
- 🤖 **多轮对话**：跨会话的记忆保持

## 📚 文档

- [技术文档](TECHNICAL_DOC.md) - 架构设计、模块详解
- [方向指引](DIRECTION.md) - 项目规划、学习路径
- [版本记录](VERSION.md) - 更新日志

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
