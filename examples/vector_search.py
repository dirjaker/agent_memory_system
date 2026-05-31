"""
示例：向量搜索
=============

演示向量存储和搜索功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector_store import create_vector_store


def main():
    print("=" * 60)
    print("示例：向量搜索")
    print("=" * 60)

    # 创建向量存储
    store = create_vector_store(dimension=64)

    # 添加文档
    documents = [
        ("doc1", "Python 是一种解释型、面向对象的高级编程语言"),
        ("doc2", "JavaScript 是 Web 开发的主要语言"),
        ("doc3", "Python 在数据科学和机器学习领域很流行"),
        ("doc4", "Rust 注重安全性和性能"),
        ("doc5", "Python 的语法简洁，适合初学者"),
    ]

    print("\n1. 添加文档:")
    for doc_id, content in documents:
        store.add(doc_id, content)
        print(f"  + {doc_id}: {content[:30]}...")

    # 搜索
    print("\n2. 搜索 'Python':")
    results = store.search_by_text("Python", top_k=3)
    for doc, score in results:
        print(f"  [{score:.3f}] {doc.content[:50]}...")

    # 统计
    print(f"\n3. 存储统计:")
    stats = store.get_stats()
    print(f"  文档数: {stats['document_count']}")
    print(f"  向量维度: {stats['dimension']}")


if __name__ == "__main__":
    main()
