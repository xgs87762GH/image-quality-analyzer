"""评估问题提示词构建器（高内聚：提示词构建逻辑集中）"""
from typing import List, Dict, Any, Optional


class EvaluationPromptBuilder:
    """评估问题提示词构建器 - 负责构建包含评估问题的AI提示词"""
    
    @staticmethod
    def build_evaluation_prompt(base_prompt: Optional[str], 
                                evaluation_questions: List[Dict[str, Any]]) -> str:
        """
        构建包含评估问题的提示词
        
        Args:
            base_prompt: 基础提示词
            evaluation_questions: 评估问题数组，格式：
                [
                    {
                        "issue": "是否为手机截图",
                        "return_type": "array",
                        "return_spec": ["是", "否"]
                    }
                ]
        
        Returns:
            增强后的提示词
        """
        if not evaluation_questions or not isinstance(evaluation_questions, list) or len(evaluation_questions) == 0:
            return base_prompt or "请分析这张图片。"
        
        # 构建评估问题部分和格式要求
        questions_text = []
        format_requirements = []
        
        for q in evaluation_questions:
            issue = q.get('issue', '')
            return_type = q.get('return_type', 'text')
            return_spec = q.get('return_spec')
            
            if not issue:
                continue
            
            questions_text.append(f"- {issue}")
            
            # 根据return_type构建格式要求
            if return_type == 'array' and isinstance(return_spec, list):
                options = '、'.join(return_spec)
                format_requirements.append(f'  "{issue}": "{options}中的一个值"')
            elif return_type == 'float' and isinstance(return_spec, dict):
                min_val = return_spec.get('min', 0)
                max_val = return_spec.get('max', 1)
                format_requirements.append(f'  "{issue}": "{min_val}-{max_val}之间的浮点数（字符串格式）"')
            elif return_type == 'text':
                format_requirements.append(f'  "{issue}": "简短文本描述"')
            else:
                format_requirements.append(f'  "{issue}": "文本"')
        
        if not questions_text:
            return base_prompt or "请分析这张图片。"
        
        evaluation_prompt = f"""

额外评估要求：
请回答以下评估问题：
{chr(10).join(questions_text)}

请严格按照以下JSON格式返回评估结果：
{{
{chr(10).join(format_requirements)}
}}

重要要求：
1. 只返回JSON对象，不要包含任何其他文字、解释或markdown代码块标记
2. 对于array类型，返回值必须是预定义选项中的一个
3. 对于float类型，返回值必须是0-1之间的浮点数（以字符串格式返回）
4. 对于text类型，返回值应该是简短的文本描述

JSON格式示例：
{{"是否为手机截图": "是", "图片质量评分": "0.85", "图片描述": "一张美丽的风景照"}}
"""
        
        if base_prompt:
            return base_prompt + evaluation_prompt
        else:
            return f"请分析这张图片。{evaluation_prompt}"
