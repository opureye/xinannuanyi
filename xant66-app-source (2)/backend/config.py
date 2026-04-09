from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

# 获取项目根目录
def get_project_root():
    # 从当前文件位置向上查找项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 当前文件在backend目录，所以需要再向上一级才能找到项目根目录
    return os.path.dirname(current_dir)

class Settings(BaseSettings):
    """应用配置类，使用Pydantic Settings管理配置"""
    
    # 应用基本信息
    app_name: str = Field("AI对话助手", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # 安全配置
    jwt_secret_key: str = Field("your-secret-key-here", env="JWT_SECRET_KEY")
    
    # 服务器配置
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8001, env="PORT")
    reload: bool = Field(False, env="RELOAD")
    
    # API配置
    api_timeout: int = Field(30, env="API_TIMEOUT")  # 秒
    api_retry_count: int = Field(2, env="API_RETRY_COUNT")
    
    # DeepSeek API配置
    deepseek_api_key: Optional[str] = Field(None, env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    
    # poloai API配置
    poloai_api_key: Optional[str] = Field(None, env="POLOAI_API_KEY")
    poloai_host: str = Field("https://poloai.top", env="POLOAI_HOST")
    
    # 默认模型配置
    default_model: str = Field("deepseek-chat", env="DEFAULT_MODEL")
    default_temperature: float = Field(0.7, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(1024, env="DEFAULT_MAX_TOKENS")
    
    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_dir: str = Field("logs", env="LOG_DIR")
    log_verbose: bool = Field(False, env="LOG_VERBOSE")
    
    # CORS配置
    cors_allow_origins: str = Field("*", env="CORS_ALLOW_ORIGINS")
    cors_allow_methods: str = Field("GET,POST,OPTIONS", env="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field("*", env="CORS_ALLOW_HEADERS")
    
    # 数据库配置
    db_path: str = Field(
        default_factory=lambda: os.path.join(get_project_root(), 'database', 'forum.db'),
        env="DB_PATH"
    )
    keys_path: str = Field(
        default_factory=lambda: os.path.join(get_project_root(), 'database', 'system_keys.json'),
        env="KEYS_PATH"
    )

    # 腾讯云实名认证配置（可选）
    tencentcloud_secret_id: Optional[str] = Field(None, env="TENCENTCLOUD_SECRET_ID")
    tencentcloud_secret_key: Optional[str] = Field(None, env="TENCENTCLOUD_SECRET_KEY")
    tencentcloud_region: str = Field("ap-guangzhou", env="TENCENTCLOUD_REGION")
    # 选择性启用腾讯云实名核验；未配置时走本地校验流程
    enable_tencent_identity_verify: bool = Field(True, env="ENABLE_TENCENT_IDENTITY_VERIFY")
    
    class Config:
        """配置类的配置"""
        # 配置文件搜索路径
        env_file = os.path.join(get_project_root(), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False

def get_settings() -> Settings:
    """
    获取配置实例（单例）
    
    :return: Settings实例
    """
    return Settings()

# 创建配置实例
settings = get_settings()

# 为了向后兼容，保留原来的导入方式
config = settings
