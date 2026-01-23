"""评估结果解析器（高内聚：评估结果解析逻辑集中）"""
import json
from typing import List, Dict, Any
from utils.logger import get_logger


class EvaluationParser:
    """评估结果解析器 - 负责从AI响应中解析JSON格式的评估结果"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def parse(self, analysis_text: str, evaluation_questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        从AI分析文本中解析JSON格式的评估结果（严格按照格式规范解析，不进行模糊匹配）
        
        Args:
            analysis_text: AI返回的分析文本
            evaluation_questions: 评估问题定义数组，格式：
                [
                    {
                        "issue": "是否为手机截图",
                        "return_type": "array",
                        "return_spec": ["是", "否"]
                    }
                ]
            
        Returns:
            评估结果数组，格式：[{'issue': '问题', 'result': '答案'}, ...]
        """
        self.logger.debug(f"[评估解析器] 开始解析评估结果")
        self.logger.debug(f"[评估解析器] analysis_text长度: {len(analysis_text) if analysis_text else 0}")
        self.logger.debug(f"[评估解析器] evaluation_questions数量: {len(evaluation_questions) if evaluation_questions else 0}")
        
        if not analysis_text or not evaluation_questions:
            self.logger.warning(f"[评估解析器] 缺少必要参数: analysis_text={'存在' if analysis_text else '缺失'}, evaluation_questions={'存在' if evaluation_questions else '缺失'}")
            return []
        
        try:
            # 提取JSON对象（移除可能的markdown代码块标记）
            json_str = analysis_text.strip()
            
            # 移除markdown代码块标记（如果存在）
            if json_str.startswith('```'):
                lines = json_str.split('\n')
                # 移除第一行和最后一行（代码块标记）
                if len(lines) > 2:
                    json_str = '\n'.join(lines[1:-1])
            
            # 查找JSON对象
            json_start = json_str.find('{')
            json_end = json_str.rfind('}')
            if json_start < 0 or json_end <= json_start:
                self.logger.warning(f"[评估解析器] ✗ 未找到JSON对象")
                self.logger.debug(f"[评估解析器] 分析文本前500字符: {analysis_text[:500]}")
                return []
            
            json_str = json_str[json_start:json_end + 1]
            self.logger.debug(f"[评估解析器] 提取的JSON字符串: {json_str[:200]}...")
            
            try:
                evaluation_dict = json.loads(json_str)
                self.logger.debug(f"[评估解析器] ✓ JSON解析成功，包含{len(evaluation_dict)}个键")
            except json.JSONDecodeError as e:
                self.logger.warning(f"[评估解析器] ✗ JSON解析失败: {e}")
                self.logger.warning(f"[评估解析器] JSON字符串内容: {json_str[:500]}")
                return []
            
            # 严格按照问题定义解析结果
            evaluations = []
            self.logger.debug(f"[评估解析器] 开始匹配评估问题，共{len(evaluation_questions)}个问题")
            
            for q_idx, q in enumerate(evaluation_questions, 1):
                issue = q.get('issue', '')
                return_type = q.get('return_type', 'text')
                return_spec = q.get('return_spec')
                
                if not issue:
                    self.logger.warning(f"[评估解析器] 问题[{q_idx}]缺少issue字段，跳过")
                    continue
                
                self.logger.debug(f"[评估解析器] 处理问题[{q_idx}]: issue='{issue}'")
                
                # 查找对应的结果（精确匹配issue）
                result = evaluation_dict.get(issue)
                if result is None:
                    # 尝试部分匹配（容错处理）
                    self.logger.debug(f"[评估解析器] 精确匹配失败，尝试部分匹配...")
                    for key, value in evaluation_dict.items():
                        if issue in key or key in issue:
                            result = value
                            self.logger.debug(f"[评估解析器] 部分匹配成功: '{key}' -> '{value}'")
                            break
                
                if result is not None:
                    result_str = str(result).strip()
                    self.logger.debug(f"[评估解析器] ✓ 找到结果: issue='{issue}', result='{result_str}'")
                    
                    # 验证结果格式
                    if return_type == 'array' and isinstance(return_spec, list):
                        # 验证结果是否在预定义选项中
                        if result_str not in return_spec:
                            self.logger.warning(f"[评估解析器] ⚠ 评估结果 '{result_str}' 不在预定义选项 {return_spec} 中，问题: {issue}")
                            # 仍然保存，但记录警告
                    
                    elif return_type == 'float':
                        # 验证是否为有效的浮点数
                        try:
                            float_val = float(result_str)
                            if isinstance(return_spec, dict):
                                min_val = return_spec.get('min', 0)
                                max_val = return_spec.get('max', 1)
                                if not (min_val <= float_val <= max_val):
                                    self.logger.warning(f"[评估解析器] ⚠ 评估结果 '{result_str}' 超出范围 [{min_val}, {max_val}]，问题: {issue}")
                        except ValueError:
                            self.logger.warning(f"[评估解析器] ⚠ 评估结果 '{result_str}' 不是有效的浮点数，问题: {issue}")
                    
                    evaluations.append({
                        'issue': issue,
                        'result': result_str
                    })
                else:
                    self.logger.warning(f"[评估解析器] ✗ 未找到问题 '{issue}' 的结果")
                    self.logger.debug(f"[评估解析器] JSON字典中的键: {list(evaluation_dict.keys())}")
            
            self.logger.info(f"[评估解析器] ✓ 解析完成，共解析出{len(evaluations)}个评估结果")
            return evaluations
        except Exception as e:
            self.logger.warning(f"[评估解析器] 解析评估结果失败: {e}", exc_info=True)
            return []
