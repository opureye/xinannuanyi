import os
import sys  # 添加sys模块导入
import random
from typing import List, Tuple, Dict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入日志模块
from backend.utils.logger import get_logger

class GDSTester:
    """
    GDS-30（老年抑郁量表）测试与评分模块
    
    该类负责：
    1. 存储GDS-30的标准问题集
    2. 定义每个问题的计分规则（正向/反向计分）
    3. 根据回答计算总分并评定抑郁等级
    4. 辅助功能：分析用户聊天风格以进行模拟测试
    """
    def __init__(self):
        # 初始化日志器
        self.logger = get_logger('gds_tester')
        self.logger.info("GDS测试模块初始化成功")
        
        # GDS-30老年抑郁量表（完整版30项）
        # 这是标准的医学量表内容
        self.gds_questions = [
            "1. 你对生活基本上满意吗？",
            "2. 你是否已经放弃了许多活动和兴趣？",
            "3. 你是否觉得生活空虚？",
            "4. 你是否常感到厌倦？",
            "5. 你觉得未来有希望吗？",
            "6. 你是否因为脑子里有一些想法摆脱不掉而烦恼？",
            "7. 你是否大部分时间精力充沛？",
            "8. 你是否害怕会有不幸的事落到你身上？",
            "9. 你是否大部分时间感到幸福？",
            "10. 你是否常感到孤立无援？",
            "11. 你是否经常坐立难安，心烦意乱？",
            "12. 你是否希望待在家里而不愿意去做些新鲜事？",
            "13. 你是否常常担心将来？",
            "14. 你是否觉得记忆力比以前差？",
            "15. 你觉得现在生活很惬意？",
            "16. 你是否常感到心情沉重、郁闷？",
            "17. 你是否觉得像现在这样生活毫无意义？",
            "18. 你是否常为过去的事忧愁？",
            "19. 你觉得生活很令人兴奋吗？",
            "20. 你开始一件新的工作困难吗？",
            "21. 你觉得生活充满活力吗？",
            "22. 你是否觉得你的处境毫无希望？",
            "23. 你是否觉得大多数人比你强的多？",
            "24. 你是否常为小事伤心？",
            "25. 你是否常觉得想哭？",
            "26. 你集中精力困难吗？",
            "27. 你早晨起的很快活吗？",
            "28. 你希望避开聚会吗？",
            "29. 你做决定很容易吗？",
            "30. 你的头脑像往常一样清晰吗？"
        ]
        # 问题计分规则：1=抑郁倾向回答，0=正常回答
        # 注意：GDS量表中部分问题是反向计分的（如"你对生活满意吗？"回答"否"才得1分）
        self.scoring_rules = [
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题1反向计分
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题5反向计分
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题7反向计分
            lambda x: 1 if x.lower() in ['是', '有', '害怕'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题9反向计分
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '希望'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '差'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题15反向计分
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题19反向计分
            lambda x: 1 if x.lower() in ['是', '有', '困难'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题21反向计分
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '是的'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '经常'] else 0,
            lambda x: 1 if x.lower() in ['是', '有', '困难'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题27反向计分
            lambda x: 1 if x.lower() in ['是', '有', '希望'] else 0,
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0,  # 问题29反向计分
            lambda x: 1 if x.lower() in ['否', '不是', '没有'] else 0   # 问题30反向计分
        ]

    def analyze_chat_style(self, chat_data: List[Dict]) -> Dict:
        """分析用户聊天风格，提取语言特征用于模拟回答"""
        self.logger.info(f"开始分析用户聊天风格，共{len(chat_data)}条消息")
        
        user_messages = self._get_user_messages(chat_data)
        if not user_messages:
            self.logger.warning("没有找到用户消息，无法分析聊天风格")
            return {'sentiment': 'neutral', 'response_length': 'medium'}
        
        # 简单情感倾向分析（基于关键词）
        positive_words = {'好', '开心', '不错', '希望', '满足', '顺利'}
        negative_words = {'累', '烦', '无聊', '害怕', '无助', '没意思'}
        pos_count = sum(1 for msg in user_messages if any(w in msg for w in positive_words))
        neg_count = sum(1 for msg in user_messages if any(w in msg for w in negative_words))
        
        # 回复长度特征
        avg_length = sum(len(msg) for msg in user_messages) / len(user_messages)
        length_type = 'short' if avg_length < 5 else 'long' if avg_length > 20 else 'medium'
        
        sentiment_result = 'positive' if pos_count > neg_count else \
                         'negative' if neg_count > pos_count else 'neutral'
        
        self.logger.info(f"聊天风格分析完成: 情感倾向={sentiment_result}, 回复长度={length_type}")
        return {
            'sentiment': sentiment_result,
            'response_length': length_type
        }

    def simulate_response(self, question: str, style: Dict) -> str:
        """基于用户聊天风格模拟GDS问题回答"""
        try:
            if style['sentiment'] == 'negative':
                negative_responses = ['是', '有时候会', '确实如此', '经常这样', '是的，我觉得']
                response = random.choice(negative_responses)
            elif style['sentiment'] == 'positive':
                positive_responses = ['不', '没有', '还好', '不太会', '我不觉得']
                response = random.choice(positive_responses)
            else:
                response = random.choice(['是', '不', '有时候会', '还好'])
            
            self.logger.info(f"模拟回答问题: {question[:20]}... 回答: {response}")
            return response
        except Exception as e:
            self.logger.error(f"模拟回答失败: {str(e)}")
            return "无法判断"

    def calculate_score(self, responses) -> Tuple[int, str, List[str]]:
        """返回得分、抑郁等级和依据列表"""
        self.logger.info(f"开始计算GDS得分，共{len(responses)}个回答")
        
        try:
            total_score = 0
            reasoning_list = []
            
            # 确保不会索引越界
            for i, resp in enumerate(responses):
                # 处理回答内容
                if isinstance(resp, tuple):
                    answer = resp[0] if resp and len(resp) > 0 else ""
                    reason = resp[1] if resp and len(resp) > 1 else "无依据"
                else:
                    # 如果不是元组，假设就是回答本身
                    answer = str(resp) if resp else ""
                    reason = "无依据"
                
                # 安全计算分数 - 加强防护
                if i < len(self.scoring_rules) and answer:
                    try:
                        # 确保answer是字符串且不为空
                        answer_str = str(answer).strip().lower()
                        # 使用更安全的方式应用scoring_rules
                        score_value = self.scoring_rules[i](answer_str)
                        # 确保得分是数字
                        total_score += int(score_value) if isinstance(score_value, (int, float)) else 0
                    except Exception as e:
                        self.logger.warning(f"计算问题{i+1}得分失败: {str(e)}，回答内容: {answer}")
                
                # 构建推理列表
                if i < len(self.gds_questions):
                    reasoning_list.append(
                        f"问题{i+1}: {self.gds_questions[i]} | 回答: {answer} | 依据: {reason}"
                    )
            
            # 获取抑郁等级
            level = self.get_level(total_score)
            self.logger.info(f"GDS得分计算完成，总分: {total_score}，抑郁等级: {level}")
            
            return total_score, level, reasoning_list
            
        except Exception as e:
            self.logger.error(f"计算GDS得分失败: {str(e)}")
            return 0, "计算失败", [f"计算失败: {str(e)}"]

    def get_level(self, score: int) -> str:
        """根据得分返回抑郁等级"""
        if score <= 10:
            return "正常"
        elif score <= 20:
            return "轻度抑郁"
        else:
            return "中重度抑郁"

    def _get_primary_user(self, chat_data: List[Dict]) -> str:
        """识别聊天记录中的主要用户（出现频率最高的发送者）"""
        self.logger.info("开始识别主要用户")
        
        if not chat_data:
            self.logger.warning("没有聊天记录数据，无法识别主要用户")
            return ""
        
        sender_counts = {}
        for msg in chat_data:
            sender = msg.get('sender', '')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        primary_user = max(sender_counts, key=sender_counts.get) if sender_counts else ""
        self.logger.info(f"主要用户识别完成: {primary_user}")
        return primary_user

    def _get_user_messages(self, chat_data: List[Dict]) -> List[str]:
        """获取主要用户的消息内容"""
        primary_user = self._get_primary_user(chat_data)
        if not primary_user:
            self.logger.warning("没有找到主要用户，无法获取用户消息")
            return []
        
        user_messages = [msg['message'] for msg in chat_data if msg.get('sender') == primary_user]
        self.logger.info(f"获取到主要用户的{len(user_messages)}条消息")
        return user_messages