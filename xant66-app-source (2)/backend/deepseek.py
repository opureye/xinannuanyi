import requests
import time
import logging
from typing import Dict, List, Any

# 配置日志
logger = logging.getLogger(__name__)

class DeepSeekAPI:
    """DeepSeek API封装类，用于与DeepSeek模型进行交互"""
    
    DEFAULT_TIMEOUT = 30  # 默认超时时间(秒)
    DEFAULT_RETRY_COUNT = 2  # 默认重试次数
    
    def __init__(self, api_key: str, base_url: str = "https://poloai.top/v1/chat/completions", timeout: int = DEFAULT_TIMEOUT, retry_count: int = DEFAULT_RETRY_COUNT):
        """
        初始化DeepSeek API客户端
        
        :param api_key: DeepSeek API密钥
        :param base_url: API基础地址
        :param timeout: 请求超时时间(秒)
        :param retry_count: 请求失败时的重试次数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理API响应，检查状态码并解析JSON
        
        :param response: API响应对象
        :return: 解析后的JSON数据
        :raises Exception: 当响应状态码不是200时抛出异常
        """
        try:
            response_data = response.json()
        except ValueError:
            logger.error(f"API响应解析失败: {response.text}")
            raise Exception(f"API响应格式错误: {response.status_code}")
        
        if not response.ok:
            error_msg = response_data.get("error", {}).get("message", "未知错误")
            logger.error(f"API请求失败: {error_msg} (状态码: {response.status_code})")
            raise Exception(f"API请求失败: {error_msg}")
        
        return response_data
    
    def _retry_request(self, func, *args, **kwargs) -> Any:
        """
        带重试机制的请求执行器
        
        :param func: 要执行的请求函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        :return: 请求结果
        :raises Exception: 重试次数耗尽后仍失败则抛出异常
        """
        retry_count = self.retry_count
        for attempt in range(retry_count + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < retry_count:
                    wait_time = (attempt + 1) * 1  # 指数退避策略
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{retry_count + 1})，{wait_time}秒后重试: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求失败，已耗尽所有重试次数: {str(e)}")
                    raise e
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "deepseek-chat",
                       temperature: float = 0.7,
                       max_tokens: int = 1024,
                       stream: bool = False) -> Dict[str, Any]:
        """
        调用聊天补全API
        """
        url = f"{self.base_url}"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        def make_request():
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                stream=stream
            )
            return self._handle_response(response)
        
        return self._retry_request(make_request)
    
    def get_models(self) -> List[Dict[str, str]]:
        """
        获取可用模型列表
        """
        url = f"{self.base_url.replace('/chat/completions', '/models')}"
        
        def make_request():
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            data = self._handle_response(response)
            return data.get("data", [])
        
        return self._retry_request(make_request)
    
    def generate_response(self, 
                         prompt: str, 
                         model: str = "deepseek-chat",
                         temperature: float = 0.7,
                         max_tokens: int = 1024) -> str:
        """
        生成对单个提示的响应
        
        :param prompt: 用户输入的提示文本
        :param model: 使用的模型名称
        :param temperature: 生成温度
        :param max_tokens: 最大生成令牌数
        :return: 模型生成的响应文本
        """
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取响应内容
            if response.get("choices") and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                raise Exception("API响应中未包含有效的生成内容")
                
        except Exception as e:
            logger.error(f"生成响应失败: {str(e)}")
            raise e
