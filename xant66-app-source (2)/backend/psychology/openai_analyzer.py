import re
import sys
import os
import logging  # 添加logging模块导入
import re  # 添加re模块导入
from typing import List, Tuple, Dict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目工具和配置
from backend.api.deepseek import DeepSeekAPI
from backend.config import get_settings
from backend.utils.logger import get_logger

class DeepSeekAnalyzer:
    """
    使用DeepSeek API进行心理评估的分析器
    
    该类负责：
    1. 管理DeepSeek API的连接和认证
    2. 构建专门的Prompt（提示词）以引导AI进行GDS-30评估
    3. 处理聊天记录上下文，生成摘要
    4. 解析AI返回的自然语言结果，提取结构化数据
    """
    
    def __init__(self):
        # 获取系统配置信息
        settings = get_settings()
        
        # 初始化日志记录器
        self.logger = get_logger('psychology_analyzer')
        
       # 初始化DeepSeek API客户端
        # 使用settings中的配置
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = "deepseek-chat"
        
        try:
            self.client = DeepSeekAPI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=settings.api_timeout,
                retry_count=settings.api_retry_count
            )
            self.logger.info(f"DeepSeek API客户端初始化成功，使用模型: {self.model}")
        except Exception as e:
            self.logger.error(f"DeepSeek API客户端初始化失败: {str(e)}")
            # 如果初始化失败，创建一个模拟客户端用于开发和测试，保证系统不崩溃
            self.client = self._create_mock_client()
    
    def _create_mock_client(self):
        """创建模拟客户端用于开发和测试"""
        class MockDeepSeekClient:
            def generate_response(self, **kwargs):
                return "是（用户聊天记录显示有抑郁倾向）\n否（用户提到了积极的计划）\n是（用户表达了孤独感）"
        
        self.logger.warning("使用模拟API客户端")
        return MockDeepSeekClient()
    
    def analyze_chat(self, chat_data: List[Dict], questions: List[str]) -> List[Tuple[str, str]]:
        """
        分析聊天记录并生成GDS回答
        
        Args:
            chat_data: 聊天记录列表
            questions: GDS-30问题列表
            
        Returns:
            List[Tuple[str, str]]: 包含(回答, 推理依据)的元组列表
        """
        if not self.api_key:
            self.logger.warning("未提供API密钥，将使用传统分析方法")
            return []
        
        try:
            # 记录开始分析时间
            self.logger.info(f"开始分析聊天记录，共{len(chat_data)}条消息")
            
            # 1. 构建聊天摘要
            # 提取核心对话内容，减少Token消耗，保留关键信息
            chat_summary = self._build_chat_summary(chat_data)
            
            # 2. 构建GDS提示
            # 使用Prompt Engineering技术，引导AI扮演心理专家角色
            prompt = self._build_gds_prompt(chat_summary, questions)
            
            # 3. 调用DeepSeek API生成响应
            # 设置temperature=0.3以保证输出的稳定性，避免过于发散
            self.logger.info("调用DeepSeek API生成分析结果")
            response_text = self.client.generate_response(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=5000
            )
            
            # 4. 解析AI响应
            # 将AI返回的自然语言文本转换为结构化的数据
            responses = self._parse_ai_responses(response_text)
            self.logger.info(f"分析完成，生成{len(responses)}个回答")
            
            return responses
            
        except Exception as e:
            self.logger.error(f"API调用失败: {str(e)}")
            return []
    
    def _build_chat_summary(self, chat_data: List[Dict]) -> str:
        """构建聊天记录摘要"""
        if not chat_data:
            self.logger.warning("没有可分析的聊天记录")
            return "无聊天记录"
        
        # 统计发言者频率，找出主要用户
        sender_counts = {}
        for msg in chat_data:
            sender = msg.get('sender', '')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        primary_user = max(sender_counts, key=sender_counts.get) if sender_counts else ""
        user_messages = [msg['message'] for msg in chat_data if msg.get('sender') == primary_user]
        
        if not user_messages:
            self.logger.warning("没有找到主要用户的消息")
            return "无聊天记录"
        
        # 限制消息数量，避免超出上下文限制
        recent_messages = user_messages[-80:] if len(user_messages) > 80 else user_messages
        summary = "\n".join(recent_messages)
        
        self.logger.info(f"构建聊天摘要完成，包含{len(recent_messages)}条消息")
        return summary
    
    def _build_gds_prompt(self, chat_summary: str, questions: List[str]) -> str:
        """
        构建GDS评估提示 (Prompt Engineering)
        
        设计思路：
        1. 角色设定：隐式要求AI作为心理评估专家
        2. 上下文注入：提供聊天记录原文作为判断依据
        3. 任务明确：要求针对30个问题逐一回答
        4. 格式规范：强制要求输出格式为"答案（依据）"，便于后续正则解析
        """
        questions_text = "\n".join(questions)
        prompt = f"""
        基于以下老年用户的聊天记录原文，请为每个GDS-30问题：
        1. 给出最符合用户心理的真实回答（是/否）
        2. 用括号注明推断依据，引用聊天记录中的具体内容
        
        聊天记录原文：
        {chat_summary}
        
        GDS-30问题列表：
        {questions_text}
        
        回答格式要求：
        每行格式：答案（依据摘要）
        示例：
        是（用户多次提到"生活没意思"）
        否（聊天记录显示用户计划旅游）
        
        请严格按格式给出30个问题的回答：
        """
        return prompt
    
    def _parse_ai_responses(self, ai_content: str) -> List[Tuple[str, str]]:
        """
        解析带推理依据的AI回答
        
        功能：
        使用正则表达式提取AI回答中的"答案"和"推理依据"。
        处理可能出现的格式偏差，保证程序的鲁棒性。
        """
        responses = []
        # 正则表达式匹配：
        # 1. 捕获组1：答案（是或否）
        # 2. 捕获组2：括号内的推理依据
        pattern = re.compile(r'^([是|否])[\s（(](.+?)[)）]?$')
        
        for line in ai_content.strip().split('\n')[:30]:
            if not line.strip():
                continue
                
            match = pattern.search(line.strip())
            if match:
                answer = match.group(1)
                reasoning = match.group(2).strip('()（）')
            else:
                # 处理格式不符合预期的情况（容错处理）
                answer = '是' if '是' in line else '否'
                reasoning = re.sub(r'^[是|否]\s*', '', line).strip()
                
            responses.append((answer, reasoning))
        
        return responses

# 为了向后兼容，保留原类名的引用
OpenAIAnalyzer = DeepSeekAnalyzer