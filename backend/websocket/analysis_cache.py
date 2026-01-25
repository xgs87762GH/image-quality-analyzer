"""
分析任务缓存（高内聚：任务缓存逻辑集中）
低耦合：通过接口与 WebSocket 服务交互

批次语义：同一 client_id 下仅有一个进行中的批次；新分析请求追加到该批次的待处理队列。
"""
import threading
import time
import queue
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger()


@dataclass
class SectionItem:
    """
    Section 中的图片项（用于前端显示加载状态和进度）
    
    Attributes:
        id: 图片ID
        status: 状态（'analyzing', 'completed', 'error'）
        timestamp: 时间戳（开始分析的时间）
    """
    id: int
    status: str
    timestamp: float


@dataclass
class AnalysisTaskStatus:
    """
    分析任务状态（高内聚：任务状态数据集中）
    
    section: 本批次正在分析的图片列表（当前在处理中的图片，包含 id、status、时间）
    pending_queue: 待分析图片 ID 队列；新追加的请求写入此处，worker 从此处取
    settings: 分析设置（用于后续追加的图片使用相同配置）
    """
    task_id: str
    session_id: str
    image_ids: List[int]  # 本批次所有图片 ID（包括已处理、正在处理、待处理）
    total: int  # 总图片数（会随追加而增长）
    success_count: int = 0
    fail_count: int = 0
    start_time: float = field(default_factory=time.time)
    image_statuses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    is_complete: bool = False
    error: Optional[str] = None
    section: List[SectionItem] = field(default_factory=list)  # 正在分析的图片列表
    pending_queue: "queue.Queue[int]" = field(default_factory=queue.Queue)  # 待分析队列
    settings: Dict[str, Any] = field(default_factory=dict)  # 分析设置


class AnalysisTaskCache:
    """
    分析任务缓存管理器（高内聚：缓存管理逻辑集中）
    低耦合：通过接口与外部交互
    """
    
    def __init__(self):
        """初始化缓存管理器"""
        self._cache: Dict[str, AnalysisTaskStatus] = {}
        self._lock = threading.Lock()
        self._logger = get_logger()
    
    def create_task(
        self,
        session_id: str,
        image_ids: List[int],
        settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建分析任务（新建批次）
        
        Args:
            session_id: 稳定客户端 ID（client_id），对应单一分析房间 analysis_{client_id}
            image_ids: 图片ID列表（会自动去重）
            settings: 分析设置（可选）
            
        Returns:
            任务ID
        """
        task_id = f"{session_id}_{int(time.time() * 1000)}"
        
        with self._lock:
            # 去重：使用 set 去重，保持顺序（Python 3.7+ dict 保持插入顺序）
            unique_image_ids = list(dict.fromkeys(image_ids))
            if len(unique_image_ids) != len(image_ids):
                self._logger.warning(
                    f"[分析缓存] 创建任务时发现重复图片ID，已去重: "
                    f"原始={len(image_ids)}, 去重后={len(unique_image_ids)}"
                )
            
            task = AnalysisTaskStatus(
                task_id=task_id,
                session_id=session_id,
                image_ids=unique_image_ids.copy(),  # 复制列表，避免外部修改
                total=len(unique_image_ids),
                settings=(settings or {}).copy(),  # 复制设置字典
            )
            # 将所有图片 ID 放入待处理队列
            for img_id in unique_image_ids:
                task.pending_queue.put(img_id)
            self._cache[task_id] = task
            self._logger.info(
                f"[分析缓存] 创建任务: task_id={task_id}, total={len(unique_image_ids)}, "
                f"pending={task.pending_queue.qsize()}"
            )
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[AnalysisTaskStatus]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态，如果不存在则返回 None
        """
        with self._lock:
            return self._cache.get(task_id)
    
    def get_task_by_session(self, session_id: str) -> Optional[AnalysisTaskStatus]:
        """
        根据 client_id（会话标识）获取任务
        
        Args:
            session_id: 稳定客户端 ID（client_id）
            
        Returns:
            任务状态，如果不存在则返回 None
        """
        with self._lock:
            for task in self._cache.values():
                if task.session_id == session_id and not task.is_complete:
                    return task
            return None
    
    def update_image_status(
        self,
        task_id: str,
        image_id: int,
        status: str,
        success: bool = False,
        error: Optional[str] = None,
        ai_warning: Optional[str] = None
    ) -> None:
        """
        更新图片状态
        
        Args:
            task_id: 任务ID
            image_id: 图片ID
            status: 状态（'analyzing', 'completed', 'error'）
            success: 是否成功
            error: 错误信息（可选）
            ai_warning: AI分析警告（可选）
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
                return
            
            task.image_statuses[image_id] = {
                "image_id": image_id,
                "status": status,
                "success": success,
                "error": error,
                "ai_warning": ai_warning,
            }
            
            # 更新计数（注意：completed/error 时 section 已在外部移除）
            if status == "completed" and success:
                task.success_count += 1
            elif status == "error":
                task.fail_count += 1
            
            self._logger.debug(
                f"[分析缓存] 更新图片状态: task_id={task_id}, image_id={image_id}, "
                f"status={status}, success={task.success_count}, failed={task.fail_count}"
            )
    
    def complete_task(self, task_id: str, error: Optional[str] = None) -> None:
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            error: 错误信息（可选）
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
                return
            
            task.is_complete = True
            task.error = error
            elapsed_time = time.time() - task.start_time
            self._logger.info(
                f"[分析缓存] 任务完成: task_id={task_id}, "
                f"success={task.success_count}, failed={task.fail_count}, "
                f"elapsed={elapsed_time:.2f}s"
            )
    
    def append_images(
        self,
        session_id: str,
        image_ids: List[int]
    ) -> Optional[str]:
        """
        追加图片到现有批次（如果存在进行中的任务）
        
        Args:
            session_id: 稳定客户端 ID（client_id）
            image_ids: 要追加的图片ID列表
            
        Returns:
            任务ID（如果成功追加），否则返回 None（表示没有进行中的批次）
        """
        with self._lock:
            # 查找进行中的任务（在锁内查找，避免并发问题）
            task = None
            for t in self._cache.values():
                if t.session_id == session_id and not t.is_complete:
                    task = t
                    break
            
            if not task:
                self._logger.debug(f"[分析缓存] 无进行中任务，无法追加: session_id={session_id}")
                return None
            
            # 去重：检查是否已在 image_ids 或 section（正在分析）中
            # 先对输入的 image_ids 去重
            unique_input_ids = list(dict.fromkeys(image_ids))
            
            # 获取正在分析的图片ID集合（从 section）
            analyzing_ids = {item.id for item in task.section}
            
            # 过滤：不在 image_ids 中，且不在 section（正在分析）中
            new_ids = [
                img_id for img_id in unique_input_ids
                if img_id not in task.image_ids and img_id not in analyzing_ids
            ]
            
            if not new_ids:
                skipped_count = len(unique_input_ids) - len(new_ids)
                self._logger.debug(
                    f"[分析缓存] 所有图片已在批次中或正在分析: task_id={task.task_id}, "
                    f"输入={len(unique_input_ids)}, 跳过={skipped_count}"
                )
                return task.task_id
            
            task.image_ids.extend(new_ids)
            task.total = len(task.image_ids)
            # 注意：pending_queue 是线程安全的，可以在锁外操作，但为了一致性在锁内操作
            for img_id in new_ids:
                task.pending_queue.put(img_id)
            
            self._logger.info(
                f"[分析缓存] 追加图片到批次: task_id={task.task_id}, "
                f"新增={len(new_ids)}, 总={task.total}, pending={task.pending_queue.qsize()}"
            )
            return task.task_id
    
    def get_next_pending(self, task_id: str, timeout: Optional[float] = None) -> Optional[int]:
        """
        从待处理队列获取下一个图片 ID（线程安全，自动跳过已在 section 中的图片）
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），None 表示不阻塞
            
        Returns:
            图片ID，如果队列为空或所有图片都在 section 中则返回 None
        """
        task = self.get_task(task_id)
        if not task:
            self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
            return None
        
        # 获取正在分析的图片ID集合（从 section）
        analyzing_ids = {item.id for item in task.section}
        
        # 循环尝试获取，直到找到不在 section 中的图片或队列为空
        max_attempts = task.pending_queue.qsize() + 1  # 最多尝试队列大小+1次
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                if timeout is None:
                    # 非阻塞
                    image_id = task.pending_queue.get_nowait()
                else:
                    # 阻塞，带超时（只在第一次尝试时使用超时）
                    image_id = task.pending_queue.get(timeout=timeout if attempts == 1 else 0.01)
                
                # 检查是否已在 section 中（正在分析）
                if image_id not in analyzing_ids:
                    return image_id
                
                # 如果已在 section 中，放回队列末尾（避免重复分析）
                task.pending_queue.put(image_id)
                self._logger.debug(
                    f"[分析缓存] 跳过已在 section 中的图片: task_id={task_id}, image_id={image_id}"
                )
                
            except queue.Empty:
                return None
        
        # 如果所有图片都在 section 中，返回 None
        return None
    
    def add_to_section(self, task_id: str, image_id: int, status: str = "analyzing") -> None:
        """
        将图片添加到 section（正在分析列表）
        
        Args:
            task_id: 任务ID
            image_id: 图片ID
            status: 状态（'analyzing', 'completed', 'error'），默认为 'analyzing'
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
                return
            
            # 检查是否已存在，如果存在则更新，否则添加
            existing_index = next(
                (i for i, item in enumerate(task.section) if item.id == image_id),
                None
            )
            
            if existing_index is not None:
                # 更新现有项
                task.section[existing_index].status = status
                task.section[existing_index].timestamp = time.time()
            else:
                # 添加新项
                task.section.append(SectionItem(
                    id=image_id,
                    status=status,
                    timestamp=time.time()
                ))
            
            self._logger.debug(
                f"[分析缓存] 添加到 section: task_id={task_id}, image_id={image_id}, "
                f"status={status}, section_size={len(task.section)}"
            )
    
    def remove_from_section(self, task_id: str, image_id: int) -> None:
        """
        从 section 移除图片（分析完成或失败）
        
        Args:
            task_id: 任务ID
            image_id: 图片ID
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
                return
            
            # 从列表中移除
            task.section = [item for item in task.section if item.id != image_id]
            
            self._logger.debug(
                f"[分析缓存] 从 section 移除: task_id={task_id}, image_id={image_id}, "
                f"section_size={len(task.section)}"
            )
    
    def update_section_status(self, task_id: str, image_id: int, status: str) -> None:
        """
        更新 section 中图片的状态
        
        Args:
            task_id: 任务ID
            image_id: 图片ID
            status: 新状态（'analyzing', 'completed', 'error'）
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                self._logger.warning(f"[分析缓存] 任务不存在: task_id={task_id}")
                return
            
            # 查找并更新
            for item in task.section:
                if item.id == image_id:
                    item.status = status
                    item.timestamp = time.time()
                    self._logger.debug(
                        f"[分析缓存] 更新 section 状态: task_id={task_id}, image_id={image_id}, "
                        f"status={status}"
                    )
                    return
            
            # 如果不存在，则添加
            self._logger.debug(
                f"[分析缓存] section 中不存在，添加: task_id={task_id}, image_id={image_id}, "
                f"status={status}"
            )
            task.section.append(SectionItem(
                id=image_id,
                status=status,
                timestamp=time.time()
            ))
    
    def get_section_size(self, task_id: str) -> int:
        """
        获取 section 大小（正在分析的图片数量）
        
        Args:
            task_id: 任务ID
            
        Returns:
            section 大小，如果任务不存在则返回 0
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                return 0
            return len(task.section)
    
    def get_section(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取 section 列表（用于前端显示）
        
        Args:
            task_id: 任务ID
            
        Returns:
            section 列表，每个元素包含 {id, status, timestamp}
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                return []
            return [
                {
                    "id": item.id,
                    "status": item.status,
                    "timestamp": item.timestamp
                }
                for item in task.section
            ]
    
    def get_all_image_statuses(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取所有图片的状态列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            图片状态列表
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                return []
            return list(task.image_statuses.values())
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> None:
        """
        清理旧任务（超过指定时间的已完成任务）
        
        Args:
            max_age_seconds: 最大保留时间（秒），默认1小时
        """
        current_time = time.time()
        with self._lock:
            tasks_to_remove = [
                task_id
                for task_id, task in self._cache.items()
                if task.is_complete and (current_time - task.start_time) > max_age_seconds
            ]
            
            for task_id in tasks_to_remove:
                del self._cache[task_id]
                self._logger.debug(f"[分析缓存] 清理旧任务: task_id={task_id}")
    
    def clear_session_tasks(self, session_id: str) -> None:
        """
        清除指定 client_id 对应的所有任务
        
        Args:
            session_id: 稳定客户端 ID（client_id）
        """
        with self._lock:
            tasks_to_remove = [
                task_id
                for task_id, task in self._cache.items()
                if task.session_id == session_id
            ]
            
            for task_id in tasks_to_remove:
                del self._cache[task_id]
                self._logger.info(f"[分析缓存] 清除会话任务: session_id={session_id}, task_id={task_id}")


# 导出单例
analysis_cache = AnalysisTaskCache()
