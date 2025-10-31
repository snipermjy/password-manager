"""
配置管理模块 - 统一管理应用配置和常量
"""
import os
from pathlib import Path
from typing import Dict, List

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 数据库配置
class DatabaseConfig:
    """数据库配置"""
    # 统一的数据库路径
    DB_DIR = PROJECT_ROOT / 'data'
    DB_PATH = DB_DIR / 'passwords.db'
    
    # 确保数据目录存在
    @classmethod
    def ensure_data_dir(cls):
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        return cls.DB_PATH

# 默认分类配置
class CategoryConfig:
    """分类配置"""
    DEFAULT_CATEGORIES = [
        {'name': '社交媒体', 'color': '#FF6B6B', 'sort_order': 1},
        {'name': '购物', 'color': '#4ECDC4', 'sort_order': 2},
        {'name': '工作', 'color': '#95E1D3', 'sort_order': 3},
        {'name': '娱乐', 'color': '#FFE66D', 'sort_order': 4},
        {'name': '金融', 'color': '#C06C84', 'sort_order': 5},
        {'name': '其他', 'color': '#999999', 'sort_order': 6}
    ]

# 默认设置配置
class SettingsConfig:
    """设置配置"""
    DEFAULT_SETTINGS = {
        'show_password': '1',
        'default_sort': 'created_at_desc',
        'smtp_server': '',
        'smtp_port': '465',
        'smtp_email': '',
        'smtp_password': '',
        'backup_email': '',
        'confirm_delete': '1',
        'extension_id_chrome': '',
        'extension_id_edge': ''
    }

# Native Messaging配置
class NativeMessagingConfig:
    """Native Messaging配置"""
    APP_NAME = 'com.mima.password_manager'
    MANIFEST_TEMPLATE = {
        "name": "com.mima.password_manager",
        "description": "Mima Password Manager Native Host",
        "type": "stdio"
    }
    
    @classmethod
    def get_manifest_dir(cls, browser='chrome'):
        """获取manifest文件目录"""
        import sys
        
        if sys.platform == 'win32':
            # Windows - 返回注册表路径
            if browser == 'chrome':
                return r'Software\Google\Chrome\NativeMessagingHosts\com.mima.password_manager'
            else:  # edge
                return r'Software\Microsoft\Edge\NativeMessagingHosts\com.mima.password_manager'
        elif sys.platform == 'darwin':
            # macOS
            if browser == 'chrome':
                return Path.home() / 'Library/Application Support/Google/Chrome/NativeMessagingHosts'
            else:  # edge
                return Path.home() / 'Library/Application Support/Microsoft Edge/NativeMessagingHosts'
        else:
            # Linux
            if browser == 'chrome':
                return Path.home() / '.config/google-chrome/NativeMessagingHosts'
            else:  # edge
                return Path.home() / '.config/microsoft-edge/NativeMessagingHosts'
    
    @classmethod
    def get_manifest_file_path(cls, browser='chrome'):
        """获取manifest文件完整路径（非Windows系统）"""
        manifest_dir = cls.get_manifest_dir(browser)
        if isinstance(manifest_dir, Path):
            return manifest_dir / f'{cls.APP_NAME}.json'
        return None  # Windows使用注册表

# 密码生成器配置
class PasswordGeneratorConfig:
    """密码生成器配置"""
    DEFAULT_LENGTH = 12
    MIN_LENGTH = 8
    MAX_LENGTH = 32
    
    UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
    DIGITS = '0123456789'
    SYMBOLS = '!@#$%^&*()_+-=[]{}|;:,.<>?'

# 搜索配置
class SearchConfig:
    """搜索配置"""
    # 搜索字段权重
    FIELD_WEIGHTS = {
        'site_name': 10,
        'login_account': 8,
        'email': 7,
        'phone': 6,
        'url': 5,
        'notes': 3
    }
    
    # 最小搜索关键词长度
    MIN_KEYWORD_LENGTH = 1
    
    # 搜索结果最大数量
    MAX_RESULTS = 100

# 备份配置
class BackupConfig:
    """备份配置"""
    # 支持的文件格式
    SUPPORTED_FORMATS = ['excel', 'csv', 'json']
    
    # 默认备份格式
    DEFAULT_FORMAT = 'excel'
    
    # 备份历史保留数量
    MAX_BACKUP_HISTORY = 50
    
    # 临时文件前缀
    TEMP_FILE_PREFIX = 'mima_backup_'

# 日志配置
class LogConfig:
    """日志配置"""
    LOG_DIR = Path.home() / '.mima' / 'logs'
    LOG_FILE = LOG_DIR / 'mima.log'
    
    @classmethod
    def ensure_log_dir(cls):
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.LOG_FILE

# 应用信息
class AppInfo:
    """应用信息"""
    NAME = "密码管理工具"
    SHORT_NAME = "Mima"
    VERSION = "1.0.0"
    ORGANIZATION = "Mima"

# 导出所有配置
__all__ = [
    'DatabaseConfig',
    'CategoryConfig', 
    'SettingsConfig',
    'NativeMessagingConfig',
    'PasswordGeneratorConfig',
    'SearchConfig',
    'BackupConfig',
    'LogConfig',
    'AppInfo',
    'PROJECT_ROOT'
]

