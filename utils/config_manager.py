"""
配置管理模块 - 管理应用配置
"""
import configparser
import os
from typing import Any, Dict


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config['Display'] = {
            'show_password': 'True',
            'window_width': '1200',
            'window_height': '800',
            'font_size': '10'
        }
        
        self.config['General'] = {
            'confirm_delete': 'True',
            'default_sort': 'created_at_desc'
        }
        
        self.config['Backup'] = {
            'smtp_server': '',
            'smtp_port': '465',
            'smtp_email': '',
            'smtp_password': '',
            'backup_email': ''
        }
        
        self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """获取配置值"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔型配置值"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数型配置值"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """设置配置值"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()
    
    def get_all_settings(self) -> Dict[str, Dict[str, str]]:
        """获取所有配置"""
        return {section: dict(self.config[section]) for section in self.config.sections()}

