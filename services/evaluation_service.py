"""评估问题服务 - 处理评估问题的业务逻辑"""
import json
from typing import List, Dict, Any, Optional
from utils.logger import get_logger


class EvaluationService:
    """评估问题服务类 - 封装评估问题的处理逻辑（高内聚）"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def create_evaluation_item(self, issue: str, result: Optional[str] = None) -> Dict[str, Any]:
        """
        创建单个评估问题项
        
        Args:
            issue: 评估问题
            result: 评估结果（可选）
            
        Returns:
            评估问题项字典
        """
        return {
            'issue': issue,
            'result': result
        }
    
    def parse_evaluation_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        解析评估问题数据
        
        支持的格式：
        1. 列表格式：[{'issue': '...', 'result': '...'}, ...]
        2. JSON字符串：'[{"issue": "...", "result": "..."}]'
        3. 单个字典：{'issue': '...', 'result': '...'}（自动转换为列表）
        
        Args:
            data: 评估问题数据（可以是列表、字典、JSON字符串或None）
            
        Returns:
            评估问题列表
        """
        if not data:
            return []
        
        # 如果是字符串，尝试解析为JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析评估问题JSON: {data}")
                return []
        
        # 如果是列表，直接返回
        if isinstance(data, list):
            return [self._normalize_item(item) for item in data if item]
        
        # 如果是字典，转换为列表
        if isinstance(data, dict):
            return [self._normalize_item(data)]
        
        return []
    
    def _normalize_item(self, item: Any) -> Dict[str, Any]:
        """
        规范化评估问题项
        
        Args:
            item: 评估问题项（可能是字典或字符串）
            
        Returns:
            规范化的评估问题项字典
        """
        if isinstance(item, dict):
            return {
                'issue': item.get('issue', ''),
                'result': item.get('result')
            }
        elif isinstance(item, str):
            # 如果是字符串，假设是issue
            return {
                'issue': item,
                'result': None
            }
        else:
            return {
                'issue': str(item) if item else '',
                'result': None
            }
    
    
    def serialize_evaluations(self, evaluations: List[Dict[str, Any]]) -> Optional[str]:
        """
        序列化评估问题列表为JSON字符串
        
        Args:
            evaluations: 评估问题列表
            
        Returns:
            JSON字符串，如果列表为空则返回None
        """
        if not evaluations:
            return None
        
        try:
            return json.dumps(evaluations, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            self.logger.error(f"序列化评估问题失败: {e}")
            return None
    
    def deserialize_evaluations(self, data: Optional[str]) -> List[Dict[str, Any]]:
        """
        反序列化JSON字符串为评估问题列表
        
        Args:
            data: JSON字符串
            
        Returns:
            评估问题列表
        """
        self.logger.debug(f"[EvaluationService.deserialize_evaluations] 输入数据: {data}, 类型: {type(data)}")
        result = self.parse_evaluation_data(data)
        self.logger.debug(f"[EvaluationService.deserialize_evaluations] 解析结果: {result}, 类型: {type(result)}, 长度: {len(result) if isinstance(result, list) else 'N/A'}")
        return result
    
    def add_evaluation_result(self, evaluations: List[Dict[str, Any]], 
                             issue: str, result: str) -> List[Dict[str, Any]]:
        """
        为指定的评估问题添加结果
        
        Args:
            evaluations: 现有评估问题列表
            issue: 评估问题
            result: 评估结果
            
        Returns:
            更新后的评估问题列表
        """
        # 查找是否已存在该问题
        for item in evaluations:
            if item.get('issue') == issue:
                item['result'] = result
                return evaluations
        
        # 如果不存在，添加新项
        evaluations.append(self.create_evaluation_item(issue, result))
        return evaluations
    
    def get_evaluation_result(self, evaluations: List[Dict[str, Any]], 
                             issue: str) -> Optional[str]:
        """
        获取指定评估问题的结果
        
        Args:
            evaluations: 评估问题列表
            issue: 评估问题
            
        Returns:
            评估结果，如果不存在则返回None
        """
        for item in evaluations:
            if item.get('issue') == issue:
                return item.get('result')
        return None
    
    def has_evaluations(self, evaluations: List[Dict[str, Any]]) -> bool:
        """
        检查是否有评估问题
        
        Args:
            evaluations: 评估问题列表
            
        Returns:
            如果有评估问题则返回True
        """
        return bool(evaluations and len(evaluations) > 0)
    
    def filter_with_results(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤出有结果的评估问题
        
        Args:
            evaluations: 评估问题列表
            
        Returns:
            有结果的评估问题列表
        """
        return [item for item in evaluations if item.get('result')]
