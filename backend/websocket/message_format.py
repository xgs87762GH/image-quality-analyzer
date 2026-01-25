"""
WebSocket 消息格式标准（高内聚：消息格式定义集中）
低耦合：通过接口与业务逻辑交互
"""
from typing import Literal, Dict, Any, Optional, List
from dataclasses import dataclass


# 业务类型定义
BusinessType = Literal['image_analysis']

# 消息状态类型
MessageStatus = Literal['success', 'error', 'progress', 'info']


@dataclass
class WebSocketMessage:
    """
    WebSocket 标准消息格式（高内聚：消息结构集中）
    
    Attributes:
        status: 消息状态（'success', 'error', 'progress', 'info'）
        message: 消息描述
        business_type: 业务类型（'image_analysis' 等）
        data: 业务数据（响应参数集合）
    """
    status: MessageStatus
    message: str
    business_type: BusinessType
    data: Dict[str, Any]


def create_message(
    status: MessageStatus,
    message: str,
    business_type: BusinessType,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建标准 WebSocket 消息
    
    Args:
        status: 消息状态
        message: 消息描述
        business_type: 业务类型
        data: 业务数据（可选）
        
    Returns:
        标准化的消息字典
    """
    return {
        "status": status,
        "message": message,
        "business_type": business_type,
        "data": data or {}
    }


def create_analysis_progress_message(
    image_id: int,
    current: int,
    total: int,
    success: int,
    failed: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    section: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    创建分析进度消息（标准化格式）
    
    Args:
        image_id: 图片ID
        current: 当前处理的图片序号
        total: 总图片数
        success: 成功数量
        failed: 失败数量
        status: 分析状态（'analyzing', 'completed', 'error'）
        result: 分析结果（可选）
        error: 错误信息（可选）
        section: 正在分析的图片列表（可选，格式：[{id, status, timestamp}]）
        
    Returns:
        标准化的分析进度消息
    """
    message_status: MessageStatus = "progress"
    message_text = "Analysis progress"
    
    if status == "completed":
        message_status = "success"
        message_text = "Image analysis completed"
    elif status == "error":
        message_status = "error"
        message_text = "Image analysis failed"
    
    data = {
        "image_id": image_id,
        "current": current,
        "total": total,
        "success": success,
        "failed": failed,
        "progress": round((current / total) * 100, 2) if total > 0 else 0,
        "analysis_status": status,  # 分析状态（'analyzing', 'completed', 'error'）
    }
    
    if result is not None:
        data["result"] = result
    if error is not None:
        data["error"] = error
    if section is not None:
        data["section"] = section  # 正在分析的图片列表
    
    return create_message(
        status=message_status,
        message=message_text,
        business_type="image_analysis",
        data=data
    )


def create_analysis_complete_message(
    total: int,
    success_count: int,
    fail_count: int,
    task_id: Optional[str] = None,
    image_statuses: Optional[list] = None,
    section: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    创建分析完成消息（标准化格式）
    
    Args:
        total: 总图片数
        success_count: 成功数量
        fail_count: 失败数量
        task_id: 任务ID（可选）
        image_statuses: 图片状态列表（可选）
        section: 正在分析的图片列表（可选，格式：[{id, status, timestamp}]）
        
    Returns:
        标准化的分析完成消息
    """
    data = {
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count,
    }
    
    if task_id:
        data["task_id"] = task_id
    if image_statuses:
        data["image_statuses"] = image_statuses
    if section is not None:
        data["section"] = section
    
    return create_message(
        status="success",
        message="Analysis complete",
        business_type="image_analysis",
        data=data
    )


def create_analysis_error_message(error: str) -> Dict[str, Any]:
    """
    创建分析错误消息（标准化格式）
    
    Args:
        error: 错误信息
        
    Returns:
        标准化的错误消息
    """
    return create_message(
        status="error",
        message="Analysis failed",
        business_type="image_analysis",
        data={"error": error}
    )


def create_analysis_started_message(
    total: int,
    task_id: Optional[str] = None,
    section: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    创建分析开始消息（标准化格式）
    
    Args:
        total: 总图片数
        task_id: 任务ID（可选）
        section: 正在分析的图片列表（可选，格式：[{id, status, timestamp}]）
        
    Returns:
        标准化的分析开始消息
    """
    data = {"total": total}
    if task_id:
        data["task_id"] = task_id
    if section is not None:
        data["section"] = section
    
    return create_message(
        status="info",
        message="Analysis started",
        business_type="image_analysis",
        data=data
    )


def create_analysis_appended_message(
    task_id: str,
    appended_count: int,
    new_total: int,
    section: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    创建分析追加消息（标准化格式）
    
    Args:
        task_id: 任务ID
        appended_count: 追加的图片数量
        new_total: 追加后的总图片数
        section: 正在分析的图片列表（可选，格式：[{id, status, timestamp}]）
        
    Returns:
        标准化的分析追加消息
    """
    data = {
        "task_id": task_id,
        "appended_count": appended_count,
        "total": new_total,
    }
    if section is not None:
        data["section"] = section
    
    return create_message(
        status="info",
        message="Images appended to batch",
        business_type="image_analysis",
        data=data
    )
