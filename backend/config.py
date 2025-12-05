# 统一配置管理文件

class Config:
    # AI模型配置
    DEFAULT_MODEL_NAME = "claude-sonnet-4-20250514"
    TITLE_GENERATION_MODEL = "claude-sonnet-4-20250514"
    
    # 数据库配置
    DEFAULT_DB_NAME = "analysis.db"
    
    # 系统配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    MAX_ITERATIONS = 100
    
    # API配置
    DEFAULT_API_TIMEOUT = 60
