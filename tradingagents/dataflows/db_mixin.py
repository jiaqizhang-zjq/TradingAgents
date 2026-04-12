"""
数据库连接共享 Mixin

将 ResearchTracker、TradingDatabase、tracker.ResearchTracker 中
完全重复的 _get_connection 上下文管理器（~15行×3 ≈ 45行重复代码）
提取为可复用的 mixin。
"""
import sqlite3
from contextlib import contextmanager
from typing import Generator

from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseMixin:
    """数据库连接共享 Mixin

    子类需提供以下属性：
    - db_path: str  — 数据库文件路径
    """

    db_path: str

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接上下文管理器

        自动处理 commit / rollback / close。
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
