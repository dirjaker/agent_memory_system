"""
示例：记忆系统基础用法
====================

演示记忆系统的各种功能：
1. 多层级记忆存储
2. 记忆流转
3. 记忆检索
4. 遗忘机制
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory_manager import create_memory_manager


def demo_basic_memory():
    """基础记忆演示"""
    print("=" * 60)
    print("示例1：基础记忆操作")
    print("=" * 60)

    # 创建记忆管理器
    manager = create_memory_manager(
        sensory_capacity=5,
        short_term_capacity=5,
        working_capacity=10,
        long_term_capacity=100
    )

    # 1. 感知输入
    print("\n1. 感知输入:")
    manager.perceive("用户问：什么是 AI Agent？")
    manager.perceive("用户问：Multi-Agent 有什么优势？")

    # 2. 主动记忆
    print("\n2. 主动记忆:")
    manager.remember(
        "AI Agent 是能够自主执行任务的智能体",
        importance=0.8,
        tags={"AI", "Agent"}
    )
    manager.remember(
        "Multi-Agent 系统可以分工协作，提高效率",
        importance=0.9,
        tags={"Multi-Agent", "协作"}
    )

    # 3. 查看统计
    stats = manager.get_stats()
    print(f"\n3. 记忆统计:")
    print(f"  感觉记忆: {stats.sensory_count}")
    print(f"  短期记忆: {stats.short_term_count}")
    print(f"  工作记忆: {stats.working_count}")
    print(f"  长期记忆: {stats.long_term_count}")

    # 4. 回忆
    print("\n4. 回忆 'Agent':")
    results = manager.recall("Agent", limit=3)
    for mem in results:
        print(f"  - [{mem.importance:.2f}] {mem.content[:50]}...")

    # 5. 获取上下文
    print("\n5. 当前上下文:")
    context = manager.get_context()
    print(context)


def demo_memory_consolidation():
    """记忆整合演示"""
    print("\n" + "=" * 60)
    print("示例2：记忆整合（短期 -> 长期）")
    print("=" * 60)

    manager = create_memory_manager()

    # 添加一些记忆
    memories = [
        ("Python 是一种解释型语言", 0.3),
        ("Python 支持面向对象编程", 0.5),
        ("Python 的 GIL 限制了多线程性能", 0.8),
        ("Python 3.12 改进了错误信息", 0.7),
        ("Python 是 AI 领域的主流语言", 0.9),
    ]

    for content, importance in memories:
        manager.remember(content, importance)

    print("\n整合前:")
    stats = manager.get_stats()
    print(f"  长期记忆: {stats.long_term_count}")

    # 执行整合
    manager.consolidate()

    print("\n整合后:")
    stats = manager.get_stats()
    print(f"  长期记忆: {stats.long_term_count}")


def demo_memory_forget():
    """遗忘演示"""
    print("\n" + "=" * 60)
    print("示例3：记忆遗忘")
    print("=" * 60)

    manager = create_memory_manager()

    # 添加记忆
    manager.remember("重要信息 1", importance=0.9)
    manager.remember("重要信息 2", importance=0.8)
    manager.remember("不太重要的信息", importance=0.2)

    print("\n遗忘前:")
    stats = manager.get_stats()
    print(f"  总记忆数: {stats.total_count}")

    # 执行遗忘
    manager.forget(hours=0)  # 立即遗忘过期记忆

    print("\n遗忘后:")
    stats = manager.get_stats()
    print(f"  总记忆数: {stats.total_count}")


if __name__ == "__main__":
    demo_basic_memory()
    demo_memory_consolidation()
    demo_memory_forget()
