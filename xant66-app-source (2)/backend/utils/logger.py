import logging
import os
from datetime import datetime
from typing import Optional

class LoggerConfig:
    """日志配置工具类，用于初始化和配置应用程序的日志系统"""
    
    # 日志格式
    _DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    _VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s"
    
    def __init__(
        self,
        log_dir: str = "logs",
        app_name: str = "ai_chat_app",
        level: int = logging.INFO,
        verbose: bool = False,
        enable_file: bool = True,
        enable_console: bool = True
    ):
        """
        初始化日志配置
        
        :param log_dir: 日志文件存储目录
        :param app_name: 应用名称，用于日志文件名
        :param level: 日志级别
        :param verbose: 是否启用详细日志格式
        :param enable_file: 是否启用文件日志
        :param enable_console: 是否启用控制台日志
        """
        self.log_dir = log_dir
        self.app_name = app_name
        self.level = level
        self.verbose = verbose
        self.enable_file = enable_file
        self.enable_console = enable_console
        
        # 确保日志目录存在
        self._ensure_log_dir()
        
        # 配置日志
        self._configure_logging()
    
    def _ensure_log_dir(self):
        """确保日志目录存在，如果不存在则创建"""
        if self.enable_file and not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except OSError as e:
                print(f"创建日志目录失败: {e}")
                self.enable_file = False  # 禁用文件日志
    
    def _get_log_file_path(self) -> str:
        """获取日志文件路径，按日期命名"""
        date_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.log_dir, f"{self.app_name}_{date_str}.log")
    
    def _configure_logging(self):
        """配置日志系统"""
        # 选择日志格式
        log_format = self._VERBOSE_FORMAT if self.verbose else self._DEFAULT_FORMAT
        formatter = logging.Formatter(log_format)
        
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)
        
        # 清除已存在的处理器，避免重复输出
        if root_logger.handlers:
            root_logger.handlers.clear()
        
        # 配置控制台日志
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 配置文件日志
        if self.enable_file:
            try:
                file_handler = logging.FileHandler(self._get_log_file_path(), encoding="utf-8")
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"配置文件日志失败: {e}")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取一个已配置的日志器实例
    
    :param name: 日志器名称，通常使用__name__
    :return: 日志器实例
    """
    return logging.getLogger(name)

# 默认日志配置
def init_default_logger():
    """初始化默认日志配置"""
    LoggerConfig(
        log_dir="logs",
        app_name="ai_chat_app",
        level=logging.INFO,
        verbose=False
    )

# 初始化默认日志配置
# 默认日志配置
init_default_logger()

# 添加setup_logger作为get_logger的别名，以保持向后兼容性
setup_logger = get_logger
