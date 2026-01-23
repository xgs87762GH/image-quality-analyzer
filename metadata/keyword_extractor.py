"""从AI分析文本中提取关键词的工具"""
import re
from typing import List, Set, Dict


def extract_keywords_from_ai_analysis(ai_analysis: str, max_keywords: int = 10) -> List[str]:
    """
    从AI分析文本中提取关键词
    
    支持多种格式：
    - 列表格式：["关键词1", "关键词2"]
    - 逗号分隔：关键词1, 关键词2, 关键词3
    - 自然语言描述：提取名词和重要形容词
    
    Args:
        ai_analysis: AI分析文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    if not ai_analysis:
        return []
    
    keywords = []
    
    # 方法1: 尝试提取JSON格式的关键词列表
    try:
        import json
        # 查找类似 ["keyword1", "keyword2"] 的模式
        json_pattern = r'\["([^"]+)"(?:\s*,\s*"([^"]+)")*\]'
        matches = re.findall(json_pattern, ai_analysis)
        if matches:
            for match in matches:
                keywords.extend([m for m in match if m])
    except:
        pass
    
    # 方法2: 查找"关键词："、"标签："等标记后的内容
    keyword_patterns = [
        r'关键词[：:]\s*([^\n]+)',
        r'标签[：:]\s*([^\n]+)',
        r'Keywords[：:]\s*([^\n]+)',
        r'Tags[：:]\s*([^\n]+)',
    ]
    
    for pattern in keyword_patterns:
        matches = re.findall(pattern, ai_analysis, re.IGNORECASE)
        for match in matches:
            # 分割逗号或分号
            parts = re.split(r'[,;，；]', match)
            keywords.extend([p.strip() for p in parts if p.strip()])
    
    # 方法3: 提取常见的中文关键词模式（2-4个字的名词）
    chinese_keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', ai_analysis)
    keywords.extend(chinese_keywords)
    
    # 方法4: 提取英文单词（排除常见停用词）
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'this', 'that', 'these', 'those', 'and', 'or', 'but', 'if',
                  'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by'}
    
    # 提取3-15个字母的单词（可能是关键词）
    english_words = re.findall(r'\b[a-zA-Z]{3,15}\b', ai_analysis)
    keywords.extend([w.lower() for w in english_words if w.lower() not in stop_words])
    
    # 去重并限制数量
    unique_keywords = []
    seen = set()
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower and kw_lower not in seen and len(kw_lower) >= 2:
            seen.add(kw_lower)
            unique_keywords.append(kw)
            if len(unique_keywords) >= max_keywords:
                break
    
    return unique_keywords


def extract_keywords_from_evaluations(evaluations: List[Dict]) -> List[str]:
    """
    从评估结果中提取关键词
    
    Args:
        evaluations: 评估结果列表
        
    Returns:
        关键词列表
    """
    keywords = []
    
    if not evaluations:
        return keywords
    
    for eval_item in evaluations:
        issue = eval_item.get('issue', '')
        result = eval_item.get('result', '')
        
        # 从issue中提取关键词
        if issue:
            # 提取2-4个字的词
            chinese_kw = re.findall(r'[\u4e00-\u9fa5]{2,4}', issue)
            keywords.extend(chinese_kw)
        
        # 从result中提取关键词（如果是数组）
        if isinstance(result, list):
            keywords.extend([str(r) for r in result if r])
        elif isinstance(result, str) and len(result) < 20:  # 短字符串可能是关键词
            keywords.append(result)
    
    # 去重
    return list(dict.fromkeys(keywords))
