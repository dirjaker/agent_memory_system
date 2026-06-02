"""
持久化层模块

使用 sqlite3 实现记忆条目的持久化存储，包括数据库初始化、
增删改查、按类型/时间范围查询、JSON 导入导出等功能。
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Any


class MemoryEntry:
    """记忆条目数据类，表示单条记忆记录。"""

    def __init__(
        self,
        id: str,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        access_count: int = 0,
        created_at: Optional[datetime] = None,
        last_accessed: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
        embedding: Optional[bytes] = None,
    ):
        # 记忆唯一标识
        self.id = id
        # 记忆内容文本
        self.content = content
        # 记忆类型（如 episodic, semantic, procedural 等）
        self.memory_type = memory_type
        # 重要性评分，范围 0.0 ~ 1.0
        self.importance = importance
        # 访问次数，用于衰减/提升权重
        self.access_count = access_count
        # 创建时间
        self.created_at = created_at or datetime.now()
        # 最后访问时间
        self.last_accessed = last_accessed or datetime.now()
        # 标签列表，用于分类检索
        self.tags = tags or []
        # 附加元数据
        self.metadata = metadata or {}
        # 嵌入向量（二进制格式）
        self.embedding = embedding


class MemoryDatabase:
    """
    SQLite 数据库管理器。

    负责数据库连接的创建、表结构初始化，以及底层 SQL 操作的封装。
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        初始化数据库连接并建表。

        Args:
            db_path: SQLite 数据库文件路径，默认为当前目录下的 memory.db
        """
        # 建立数据库连接，check_same_thread=False 允许多线程访问
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = sqlite3.connect(
            db_path, check_same_thread=False
        )
        # 启用 WAL 模式以提升并发读写性能
        self.conn.execute("PRAGMA journal_mode=WAL")
        # 设置返回行类型为 Row，方便按列名访问
        self.conn.row_factory = sqlite3.Row
        # 初始化表结构
        self._init_db()

    def _init_db(self) -> None:
        """
        创建 memories 表（如果尚不存在）。

        表结构说明：
          - id:             TEXT 主键，UUID 格式
          - content:        TEXT 记忆内容
          - memory_type:    TEXT 记忆类型
          - importance:     REAL 重要性评分
          - access_count:   INTEGER 访问次数
          - created_at:     TEXT 创建时间（ISO 8601 格式）
          - last_accessed:  TEXT 最后访问时间
          - tags:           TEXT 标签（JSON 数组序列化存储）
          - metadata:       TEXT 元数据（JSON 对象序列化存储）
          - embedding:      BLOB 嵌入向量
        """
        sql = """
        CREATE TABLE IF NOT EXISTS memories (
            id            TEXT PRIMARY KEY,
            content       TEXT NOT NULL,
            memory_type   TEXT NOT NULL DEFAULT 'general',
            importance    REAL NOT NULL DEFAULT 0.5,
            access_count  INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            tags          TEXT DEFAULT '[]',
            metadata      TEXT DEFAULT '{}',
            embedding     BLOB
        )
        """
        self.conn.execute(sql)
        # 为 memory_type 和 created_at 创建索引以加速查询
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)"
        )
        self.conn.commit()

    def close(self) -> None:
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            self.conn = None


class MemoryRepository:
    """
    记忆仓库，提供对 MemoryEntry 的持久化 CRUD 操作。

    内部依赖 MemoryDatabase 管理数据库连接和表结构。
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        初始化记忆仓库。

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db = MemoryDatabase(db_path)

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """
        将数据库查询结果行转换为 MemoryEntry 对象。

        Args:
            row: sqlite3.Row 查询结果行

        Returns:
            MemoryEntry 实例
        """
        # 解析标签：从 JSON 字符串还原为列表
        tags = json.loads(row["tags"]) if row["tags"] else []
        # 解析元数据：从 JSON 字符串还原为字典
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            memory_type=row["memory_type"],
            importance=row["importance"],
            access_count=row["access_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]),
            tags=tags,
            metadata=metadata,
            embedding=row["embedding"],
        )

    def _entry_to_params(self, entry: MemoryEntry) -> tuple:
        """
        将 MemoryEntry 对象序列化为数据库插入所需的参数元组。

        Args:
            entry: MemoryEntry 实例

        Returns:
            包含所有字段值的元组
        """
        return (
            entry.id,
            entry.content,
            entry.memory_type,
            entry.importance,
            entry.access_count,
            entry.created_at.isoformat(),
            entry.last_accessed.isoformat(),
            json.dumps(entry.tags, ensure_ascii=False),
            json.dumps(entry.metadata, ensure_ascii=False),
            entry.embedding,
        )

    # ------------------------------------------------------------------
    # CRUD 操作
    # ------------------------------------------------------------------

    def save(self, entry: MemoryEntry, memory_type: str = "general") -> None:
        """
        保存或更新一条记忆条目。

        如果相同 id 已存在则覆盖（使用 INSERT OR REPLACE）。

        Args:
            entry:       要保存的 MemoryEntry 实例
            memory_type: 记忆类型（会同步更新到 entry 对象）
        """
        # 同步 memory_type
        entry.memory_type = memory_type
        sql = """
        INSERT OR REPLACE INTO memories
            (id, content, memory_type, importance, access_count,
             created_at, last_accessed, tags, metadata, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.conn.execute(sql, self._entry_to_params(entry))
        self.db.conn.commit()

    def load(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        根据 id 加载一条记忆条目。

        加载时会自动累加 access_count 并更新 last_accessed。

        Args:
            memory_id: 记忆条目的唯一标识

        Returns:
            对应的 MemoryEntry 对象，若不存在则返回 None
        """
        cursor = self.db.conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        # 更新访问计数和时间戳
        self.db.conn.execute(
            "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
            (datetime.now().isoformat(), memory_id),
        )
        self.db.conn.commit()
        return self._row_to_entry(row)

    def delete(self, memory_id: str) -> bool:
        """
        根据 id 删除一条记忆条目。

        Args:
            memory_id: 记忆条目的唯一标识

        Returns:
            True 表示成功删除，False 表示未找到对应条目
        """
        cursor = self.db.conn.execute(
            "DELETE FROM memories WHERE id = ?", (memory_id,)
        )
        self.db.conn.commit()
        # rowcount > 0 说明确实删除了记录
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # 查询方法
    # ------------------------------------------------------------------

    def query_by_type(
        self, memory_type: str, limit: int = 100
    ) -> List[MemoryEntry]:
        """
        按记忆类型查询条目列表。

        结果按重要性降序排列，最多返回 limit 条。

        Args:
            memory_type: 要查询的记忆类型
            limit:       最大返回条数，默认 100

        Returns:
            符合条件的 MemoryEntry 列表
        """
        cursor = self.db.conn.execute(
            "SELECT * FROM memories WHERE memory_type = ? ORDER BY importance DESC LIMIT ?",
            (memory_type, limit),
        )
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def query_by_timerange(
        self, start: datetime, end: datetime
    ) -> List[MemoryEntry]:
        """
        按创建时间范围查询记忆条目。

        查询 created_at 落在 [start, end] 区间内的所有记录。

        Args:
            start: 起始时间（含）
            end:   结束时间（含）

        Returns:
            符合条件的 MemoryEntry 列表，按创建时间升序排列
        """
        cursor = self.db.conn.execute(
            "SELECT * FROM memories WHERE created_at >= ? AND created_at <= ? ORDER BY created_at ASC",
            (start.isoformat(), end.isoformat()),
        )
        return [self._row_to_entry(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """
        返回数据库中记忆条目的总数。

        Returns:
            记忆条目总数
        """
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]

    # ------------------------------------------------------------------
    # 导入 / 导出
    # ------------------------------------------------------------------

    def export_json(self, path: str) -> None:
        """
        将所有记忆条目导出为 JSON 文件。

        导出格式为 JSON 数组，每个元素是一条记忆的字典表示。

        Args:
            path: 导出文件的路径
        """
        cursor = self.db.conn.execute("SELECT * FROM memories ORDER BY created_at")
        rows = cursor.fetchall()
        entries = []
        for row in rows:
            entry = self._row_to_entry(row)
            entries.append({
                "id": entry.id,
                "content": entry.content,
                "memory_type": entry.memory_type,
                "importance": entry.importance,
                "access_count": entry.access_count,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "tags": entry.tags,
                "metadata": entry.metadata,
                # embedding 不导出（二进制数据不适合 JSON）
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def import_json(self, path: str) -> None:
        """
        从 JSON 文件导入记忆条目。

        文件格式应为 export_json 导出的 JSON 数组。导入时使用
        INSERT OR REPLACE，已存在的 id 会被覆盖。

        Args:
            path: 导入文件的路径
        """
        with open(path, "r", encoding="utf-8") as f:
            entries_data = json.load(f)
        for data in entries_data:
            entry = MemoryEntry(
                id=data.get("id", str(uuid.uuid4())),
                content=data["content"],
                memory_type=data.get("memory_type", "general"),
                importance=data.get("importance", 0.5),
                access_count=data.get("access_count", 0),
                created_at=datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(),
                last_accessed=datetime.fromisoformat(data["last_accessed"])
                if "last_accessed" in data
                else datetime.now(),
                tags=data.get("tags", []),
                metadata=data.get("metadata", {}),
            )
            self.save(entry, entry.memory_type)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def close(self) -> None:
        """关闭底层数据库连接，释放资源。"""
        self.db.close()
