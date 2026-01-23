"""仓库基类 - 定义数据访问层的通用接口"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from database.connection import DatabaseConnection


class BaseRepository(ABC):
    """仓库基类 - 所有仓库都应继承此类"""
    
    def __init__(self, db: 'DatabaseConnection'):
        """
        初始化仓库
        
        Args:
            db: 数据库连接
        """
        self.db = db
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """
        创建实体
        
        Args:
            entity: 实体对象
            
        Returns:
            创建后的实体对象（包含ID）
        """
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[Any]:
        """
        根据ID查找实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> bool:
        """
        更新实体
        
        Args:
            entity: 实体对象
            
        Returns:
            更新成功返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            删除成功返回True，否则返回False
        """
        pass
