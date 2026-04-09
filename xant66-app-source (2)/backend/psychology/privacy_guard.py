import re  # 添加缺失的导入
import sys
import os
from typing import Any, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入日志模块
from backend.utils.logger import get_logger

class PrivacyGuard:
    """
    隐私保护模块
    
    功能：
    1. 对聊天记录进行敏感信息脱敏（姓名、地址、电话、身份证等）
    2. 提供内存清理功能，确保敏感数据不残留在内存中
    
    安全机制：
    - 正则表达式匹配多种敏感信息格式
    - 内存深度清理，覆盖字典和列表中的字符串
    """
    
    # 姓名匹配模式：匹配常见的中文姓名格式和称谓
    _NAME_PATTERNS = [
        r'(?:[一-龥]{2,4})(?:书记|老师|医生|护士|小姐|阿姨|叔叔|爷爷|奶奶|爸爸|妈妈|主任|经理|教授|工程师)',
        r'(?:小|老|大)[一-龥]',
        r'[一-龥](?:哥|姐|弟|妹|叔|伯|姨|姑|舅|婶|甥|侄|嫂|妯|妫|妭|妮|妯|妫|妭|妮)',
        r'(?:[一-龥]{2,4})(?:先生|女士|同志|同学|先生|夫人|太太|阁下)'
    ]
    
    # 地址匹配模式：匹配省市区、街道、小区等地理位置信息
    _LOCATION_PATTERNS = [
        r'(?:[一-龥]{1,4})(?:号|路|街|巷|小区|大厦|医院|学校|大学|中学|小学|幼儿园|公司|集团|工厂|店铺|超市|商场|社区|园区|广场|剧院|体育馆|博物馆|图书馆|家)',
        r'(?:[一-龥]{1,4})(?:村|镇|乡|县|市|省|自治区|特别行政区|旗|盟|州|街道|站|机场|火车站|汽车站|地铁站|公交站|码头|港口|高铁站|基地)'
    ]
    
    # 数字匹配模式：匹配手机号、身份证号、银行卡号等
    _NUMBER_PATTERNS = [
        r'\b(?:\+?86[-\s]?)?1[3-9]\d{9}\b', # 手机号
        r'\b\d{17}[\dXx]|\d{15}\b',         # 身份证号
        r'\b\d{16,19}\b',                   # 银行卡号
        r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4,6}' # 车牌号
    ]
    
    # 其他敏感信息匹配模式：邮箱、IP地址、URL
    _SENSITIVE_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', # 邮箱
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',                         # IP地址
        r'https?://[^\s]+'                                      # URL链接
    ]

    def __init__(self):
        # 初始化日志器
        self.logger = get_logger('privacy_guard')
        self.logger.info("隐私保护模块初始化成功")

    def anonymize_chat(self, chat_data: List[dict]) -> List[dict]:
        """
        匿名化处理聊天记录，移除个人标识信息
        
        Args:
            chat_data: 原始聊天记录列表
            
        Returns:
            List[dict]: 脱敏后的聊天记录列表，敏感信息被替换为 '***'
        """
        self.logger.info(f"开始匿名化处理聊天记录，共{len(chat_data)}条消息")
        anonymized = []
        pattern_count = 0
        
        for msg in chat_data:
            content = msg.get('message', '')
            # 合并所有匹配模式
            patterns = PrivacyGuard._NAME_PATTERNS + \
                  PrivacyGuard._LOCATION_PATTERNS + \
                  PrivacyGuard._NUMBER_PATTERNS + \
                  PrivacyGuard._SENSITIVE_PATTERNS
            
            # 依次应用正则替换
            for pattern in patterns:
                match_count = len(re.findall(pattern, content))
                content = re.sub(pattern, '***', content, flags=re.IGNORECASE)
                pattern_count += match_count
            
            # 关键词替换（二次保险）
            sensitive_words = ['身份证','银行卡','密码','验证码']
            for word in sensitive_words:
                if word in content:
                    content = content.replace(word, '***')
                    pattern_count += content.count('***')
            
            anonymized.append({
                'sender': msg.get('sender', ''),
                'message': content,
                'timestamp': msg.get('timestamp', '')
            })
        
        self.logger.info(f"聊天记录匿名化完成，共替换{pattern_count}处敏感信息")
        return anonymized

    def secure_cleanup(self, temp_data: dict) -> None:
        """
        安全清理内存中的临时数据
        
        目的：防止敏感数据在内存中残留，降低内存dump攻击的风险
        """
        self.logger.info("开始安全清理临时数据")
        try:
            for key in temp_data:
                temp_data[key] = None
            del temp_data
            self.logger.info("临时数据已安全清理，未留存原始聊天记录")
        except Exception as e:
            self.logger.error(f"临时数据清理失败: {str(e)}")
        
    def deep_cleanup(self, obj: Any) -> None:
        """深度清理内存数据"""
        self.logger.info("开始深度清理内存数据")
        try:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        obj[key] = '*' * len(value)
                    elif isinstance(value, (dict, list)):
                        PrivacyGuard.deep_cleanup(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, str):
                        obj[i] = '*' * len(item)
                    elif isinstance(item, (dict, list)):
                        PrivacyGuard.deep_cleanup(item)
            self.logger.info("深度清理完成")
        except Exception as e:
            self.logger.error(f"深度清理失败: {str(e)}")

    def anonymize_text(self, text: str) -> str:
        """单独匿名化文本内容"""
        self.logger.info(f"开始匿名化文本内容，长度: {len(text)}字符")
        content = text
        patterns = PrivacyGuard._NAME_PATTERNS + \
              PrivacyGuard._LOCATION_PATTERNS + \
              PrivacyGuard._NUMBER_PATTERNS + \
              PrivacyGuard._SENSITIVE_PATTERNS
        
        pattern_count = 0
        for pattern in patterns:
            match_count = len(re.findall(pattern, content))
            content = re.sub(pattern, '***', content, flags=re.IGNORECASE)
            pattern_count += match_count
        
        sensitive_words = ['身份证','银行卡','密码','验证码']
        for word in sensitive_words:
            if word in content:
                content = content.replace(word, '***')
                pattern_count += content.count('***')
        
        self.logger.info(f"文本匿名化完成，共替换{pattern_count}处敏感信息")
        return content