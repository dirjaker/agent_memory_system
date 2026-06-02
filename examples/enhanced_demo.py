"""
Enhanced Demo — v2.0 完整功能演示
===================================

演示 Agent Memory System v2.0 的所有新功能：
- 创建 MemoryManager（新配置）
- 感知输入 -> 短期记忆
- 主动记忆 -> 工作记忆
- 情景记忆（对话历史）
- 语义记忆（事实知识）
- 自动整合记忆
- 混合检索
- 生成 LLM 上下文
- SQLite 持久化
- 可观测性报告
"""

import os
import sys
import json

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import create_memory_manager


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    # ----------------------------------------------------------------
    # 1. 创建 MemoryManager
    # ----------------------------------------------------------------
    separator("1. 创建 MemoryManager")
    manager = create_memory_manager(
        sensory_capacity=5,
        short_term_capacity=10,
        working_capacity=20,
        long_term_capacity=500,
    )
    print("✅ MemoryManager 创建成功")
    print(f"   感觉记忆容量: 5")
    print(f"   短期记忆容量: 10")
    print(f"   工作记忆容量: 20")
    print(f"   长期记忆容量: 500")

    # ----------------------------------------------------------------
    # 2. 感知输入 -> 短期记忆
    # ----------------------------------------------------------------
    separator("2. 感知输入 -> 短期记忆")
    inputs = [
        "用户问：Python 和 Java 哪个更适合 AI 开发？",
        "用户说：我想构建一个聊天机器人。",
        "用户问：什么是 Transformer？",
    ]
    for inp in inputs:
        entry = manager.perceive(inp)
        print(f"  📥 感知: {inp}")
        print(f"     -> 短期记忆 ID: {entry.id[:8]}...")

    # ----------------------------------------------------------------
    # 3. 主动记忆 -> 工作记忆
    # ----------------------------------------------------------------
    separator("3. 主动记忆 -> 工作记忆")
    memories = [
        ("Python 是 AI 领域最流行的编程语言", 0.8, {"Python", "AI"}),
        ("Transformer 是 Google 2017 年提出的模型", 0.9, {"Transformer", "深度学习"}),
        ("聊天机器人通常使用 seq2seq 或 LLM 实现", 0.7, {"chatbot", "NLP"}),
        ("LangChain 是一个 LLM 应用开发框架", 0.6, {"LangChain", "工具"}),
    ]
    for content, importance, tags in memories:
        entry = manager.remember(content, importance=importance, tags=tags)
        print(f"  💾 记忆: {content}")
        print(f"     重要性: {importance}, 标签: {tags}")

    # ----------------------------------------------------------------
    # 4. 情景记忆 — 对话历史
    # ----------------------------------------------------------------
    separator("4. 情景记忆（对话历史）")
    conversation = [
        ("conv_001", "user", "你好，我想了解一下 Python。"),
        ("conv_001", "assistant", "你好！Python 是一种通用编程语言，特别适合 AI 开发。"),
        ("conv_001", "user", "Python 和 Java 哪个更适合机器学习？"),
        ("conv_001", "assistant", "Python 有更丰富的 ML 生态（PyTorch、scikit-learn 等），推荐使用 Python。"),
        ("conv_002", "user", "什么是 Transformer 模型？"),
        ("conv_002", "assistant", "Transformer 是 2017 年 Google 提出的基于自注意力机制的模型。"),
    ]
    for conv_id, role, content in conversation:
        manager.add_episodic(conv_id, role, content)
        role_icon = "👤" if role == "user" else "🤖"
        print(f"  {role_icon} [{conv_id}] {role}: {content}")

    print(f"\n  共记录 {len(conversation)} 轮对话")

    # ----------------------------------------------------------------
    # 5. 语义记忆 — 事实知识
    # ----------------------------------------------------------------
    separator("5. 语义记忆（事实知识）")
    facts = [
        ("Python 是一种高级编程语言", ["Python"]),
        ("PyTorch 是 Meta 开发的深度学习框架", ["PyTorch"]),
        ("TensorFlow 是 Google 开发的深度学习框架", ["TensorFlow"]),
        ("GPT 是 OpenAI 开发的大语言模型", ["GPT"]),
        ("Transformer 使用自注意力机制", ["Transformer"]),
    ]
    for content, entities in facts:
        manager.add_semantic(content, entities=entities)
        print(f"  🏷️  事实: {content}  (实体: {entities})")

    # ----------------------------------------------------------------
    # 6. 自动整合记忆
    # ----------------------------------------------------------------
    separator("6. 自动整合记忆")
    print("  整合前统计:")
    stats_before = manager.get_stats()
    print(f"    短期: {stats_before.short_term_count}, "
          f"工作: {stats_before.working_count}, "
          f"长期: {stats_before.long_term_count}")

    count = manager.auto_consolidate()
    print(f"\n  ✅ 自动整合完成: {count} 条记忆从短期转入长期")

    stats_after = manager.get_stats()
    print(f"  整合后统计:")
    print(f"    短期: {stats_after.short_term_count}, "
          f"工作: {stats_after.working_count}, "
          f"长期: {stats_after.long_term_count}")

    # ----------------------------------------------------------------
    # 7. 混合检索
    # ----------------------------------------------------------------
    separator("7. 混合检索")
    queries = ["Python", "Transformer", "聊天机器人", "深度学习框架"]
    for query in queries:
        print(f"  🔍 查询: \"{query}\"")
        results = manager.search_memories(query, limit=3)
        if results:
            for i, r in enumerate(results, 1):
                print(f"     {i}. [{r.source}] (score={r.score:.3f}) {r.content[:60]}")
        else:
            print("     （无结果）")
        print()

    # ----------------------------------------------------------------
    # 8. 生成 LLM 上下文
    # ----------------------------------------------------------------
    separator("8. 生成 LLM 上下文")
    query = "Python"
    print(f"  查询: \"{query}\"")
    llm_context = manager.get_context_for_llm(query=query, limit=5)
    print(f"  LLM 上下文 ({len(llm_context)} 字符):")
    print("  " + "-" * 50)
    for line in llm_context.split("\n"):
        print(f"  {line}")
    print("  " + "-" * 50)

    # ----------------------------------------------------------------
    # 9. SQLite 持久化
    # ----------------------------------------------------------------
    separator("9. SQLite 持久化")
    db_path = "enhanced_demo_memory.db"

    # 保存
    manager.save_to_db(db_path)
    print(f"  ✅ 记忆已保存到 {db_path}")

    # 创建新管理器并加载
    manager2 = create_memory_manager()
    manager2.load_from_db(db_path)
    print(f"  ✅ 记忆已从 {db_path} 加载")

    # 验证
    stats2 = manager2.get_stats()
    print(f"  加载后统计: 短期={stats2.short_term_count}, "
          f"工作={stats2.working_count}, "
          f"长期={stats2.long_term_count}")

    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  🧹 已清理临时文件 {db_path}")

    # ----------------------------------------------------------------
    # 10. 可观测性报告
    # ----------------------------------------------------------------
    separator("10. 可观测性报告")
    report = manager.get_observability_report()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    # ----------------------------------------------------------------
    # 完成
    # ----------------------------------------------------------------
    separator("✅ Demo 完成")
    print("  所有 v2.0 功能演示完毕！")
    print()
    print("  已演示功能:")
    print("    ✓ 感知输入 -> 短期记忆")
    print("    ✓ 主动记忆 -> 工作记忆（高重要性自动入长期）")
    print("    ✓ 情景记忆（对话历史）")
    print("    ✓ 语义记忆（事实知识）")
    print("    ✓ 自动整合（短期 -> 长期）")
    print("    ✓ 混合检索（多层级 + 多来源）")
    print("    ✓ LLM 上下文生成")
    print("    ✓ SQLite 持久化（保存 + 加载）")
    print("    ✓ 可观测性报告")
    print()


if __name__ == "__main__":
    main()
