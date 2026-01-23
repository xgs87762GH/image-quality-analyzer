"""AI图像分析器 - 支持多种AI模型（高内聚：AI分析协调逻辑集中）"""
from typing import Dict, Any, Optional, List
from pathlib import Path

from analyzers.base_analyzer import BaseAnalyzer
from analyzers.prompts.evaluation_prompt_builder import EvaluationPromptBuilder
from analyzers.parsers.evaluation_parser import EvaluationParser
from analyzers.ai_models.base_model import BaseAIModel
from analyzers.ai_models.gpt4v_model import GPT4VModel
from analyzers.ai_models.claude_model import ClaudeModel
from analyzers.ai_models.gemini_model import GeminiModel
from analyzers.ai_models.ollama_model import OllamaModel
from utils.logger import get_logger


class AIAnalyzer(BaseAnalyzer):
    """AI图像分析器 - 协调多种AI模型进行分析（低耦合：通过模型接口交互）"""
    
    def __init__(self, model: str = "gpt4v", api_key: Optional[str] = None, 
                 ollama_base_url: Optional[str] = None, ollama_model: Optional[str] = None):
        """
        初始化AI分析器
        
        Args:
            model: 模型名称 (gpt4v, claude, gemini, ollama)
            api_key: API密钥（对于云端模型）
            ollama_base_url: Ollama API地址（默认 http://localhost:11434）
            ollama_model: Ollama模型名称（如 llama2, mistral, codellama等）
        """
        self.model_name = model
        self.api_key = api_key
        self.ollama_base_url = ollama_base_url or "http://localhost:11434"
        self.ollama_model = ollama_model or "llama2"
        self.logger = get_logger()
        
        # 初始化模型实例（低耦合：通过接口交互）
        self._ai_model = self._create_model_instance()
        self._prompt_builder = EvaluationPromptBuilder()
        self._evaluation_parser = EvaluationParser()
    
    def _create_model_instance(self) -> Optional[BaseAIModel]:
        """
        创建AI模型实例（工厂方法模式）
        
        Returns:
            AI模型实例，如果模型不支持则返回None
        """
        if self.model_name == "gpt4v":
            return GPT4VModel(self.api_key) if self.api_key else None
        elif self.model_name == "claude":
            return ClaudeModel(self.api_key) if self.api_key else None
        elif self.model_name == "gemini":
            return GeminiModel(self.api_key) if self.api_key else None
        elif self.model_name == "ollama":
            return OllamaModel(self.ollama_base_url, self.ollama_model)
        else:
            return None
    
    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self._ai_model is not None and self._ai_model.is_available()
    
    def analyze(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        分析图像（实现BaseAnalyzer接口）
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            分析结果字典
        """
        result = self.analyze_image(image_path)
        if result.get('success'):
            return {
                'analysis': result.get('analysis'),
                'evaluations': result.get('evaluations', [])
            }
        return None
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None, 
                     evaluation_questions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        使用AI分析图像
        
        Args:
            image_path: 图像路径
            prompt: 自定义提示词
            evaluation_questions: 评估问题数组，格式：
                [
                    {
                        "issue": "是否为手机截图",
                        "return_type": "array",
                        "return_spec": ["是", "否"]
                    }
                ]
            
        Returns:
            分析结果，包含：
            - success: 是否成功
            - analysis: 分析文本
            - evaluations: 评估结果数组，格式：[{'issue': '问题', 'result': '答案'}, ...]
        """
        if not Path(image_path).exists():
            return {'success': False, 'error': '图像文件不存在'}
        
        if not self.is_available():
            return {'success': False, 'error': f'AI模型不可用: {self.model_name}'}
        
        try:
            # 构建包含评估问题的提示词（高内聚：提示词构建逻辑集中）
            enhanced_prompt = self._prompt_builder.build_evaluation_prompt(
                prompt, evaluation_questions or []
            )
            
            # 调用AI模型进行分析（低耦合：通过接口调用）
            ai_result = self._ai_model.analyze(image_path, enhanced_prompt)
            
            if not ai_result.get('success'):
                return ai_result
            
            analysis_text = ai_result.get('analysis', '')
            
            # 解析评估结果（高内聚：评估结果解析逻辑集中）
            evaluations = []
            if evaluation_questions:
                evaluations = self._evaluation_parser.parse(analysis_text, evaluation_questions)
            
            return {
                'success': True,
                'model': self.model_name,
                'analysis': analysis_text,
                'evaluations': evaluations,
                'raw_response': ai_result.get('raw_response')
            }
        except Exception as e:
            self.logger.error(f"AI分析失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def calculate_aesthetic_score(self, image_path: str) -> Optional[float]:
        """
        使用AI模型评估图像的审美质量
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            审美评分（0-10），如果失败则返回None
        """
        if not Path(image_path).exists():
            self.logger.warning(f"图像文件不存在: {image_path}")
            return None
        
        # 详细的审美评估提示词
        aesthetic_prompt = """请评估这张图片的审美质量，从以下维度进行评分（每个维度0-10分）：
1. 构图：画面布局、主体位置、视觉平衡
2. 色彩：色彩搭配、饱和度、色调和谐度
3. 光影：光线运用、明暗对比、层次感
4. 整体美感：综合视觉效果、艺术性、吸引力

请给出一个综合审美分数（0-10分），只返回分数数字，不要其他文字。
例如：如果图片很美，返回 8.5；如果一般，返回 5.0；如果较差，返回 3.0。
只返回一个数字，不要任何解释。"""
        
        try:
            # 使用现有的analyze_image方法，但使用专门的审美评估提示词
            result = self.analyze_image(image_path, prompt=aesthetic_prompt)
            
            if not result.get('success'):
                self.logger.warning(f"AI审美评估失败: {result.get('error', '未知错误')}")
                return None
            
            # 从AI响应中提取分数
            analysis_text = result.get('analysis', '')
            if not analysis_text:
                self.logger.warning("AI审美评估返回空结果")
                return None
            
            # 尝试从文本中提取数字（0-10之间的浮点数）
            import re
            # 匹配0-10之间的数字（包括小数）
            score_pattern = r'\b([0-9](?:\.[0-9]+)?|10(?:\.0+)?)\b'
            matches = re.findall(score_pattern, analysis_text)
            
            if matches:
                # 取第一个匹配的数字
                score = float(matches[0])
                # 确保分数在0-10范围内
                score = max(0.0, min(10.0, score))
                self.logger.info(f"AI审美评估成功: {score} (来源: {analysis_text[:50]}...)")
                return score
            else:
                # 如果没有找到数字，尝试从文本中推断
                # 检查是否包含"美"、"好"等正面词汇
                positive_keywords = ['美', '好', '优秀', '出色', '精美', '漂亮', '吸引', '艺术']
                negative_keywords = ['差', '糟糕', '普通', '一般', '平淡', '无趣']
                
                text_lower = analysis_text.lower()
                positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
                negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
                
                if positive_count > negative_count:
                    # 正面评价，给一个中等偏高的分数
                    estimated_score = 7.0
                elif negative_count > positive_count:
                    # 负面评价，给一个中等偏低的分数
                    estimated_score = 4.0
                else:
                    # 中性评价
                    estimated_score = 5.5
                
                self.logger.warning(f"无法从AI响应中提取数字分数，使用估算值: {estimated_score}")
                return estimated_score
                
        except Exception as e:
            self.logger.error(f"AI审美评估异常: {str(e)}", exc_info=True)
            return None
    
    def get_ollama_models(self) -> Dict[str, Any]:
        """
        获取Ollama可用模型列表
        
        Returns:
            模型列表
        """
        if self.model_name == "ollama" and isinstance(self._ai_model, OllamaModel):
            return self._ai_model.get_models()
        else:
            return {
                'success': False,
                'error': '当前模型不是Ollama'
            }
