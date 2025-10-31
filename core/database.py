"""
数据库操作模块 - 处理所有数据库交互
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from .models import Password, Category, CustomField, ModificationHistory, BackupHistory
from .config import DatabaseConfig, CategoryConfig, SettingsConfig, LogConfig

# 配置日志
LogConfig.ensure_log_dir()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LogConfig.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库连接"""
        # 使用统一的配置路径
        if db_path is None:
            self.db_path = str(DatabaseConfig.ensure_data_dir())
        else:
            self.db_path = db_path
        
        logger.info(f"初始化数据库: {self.db_path}")
        self.ensure_data_directory()
        self.init_database()
    
    def ensure_data_directory(self):
        """确保data目录存在"""
        dir_path = os.path.dirname(self.db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        return conn
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建passwords表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_name TEXT NOT NULL,
                    url TEXT,
                    login_account TEXT,
                    password TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    category TEXT,
                    notes TEXT,
                    register_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT 0,
                    deleted_at TIMESTAMP
                )
            ''')
            
            # 创建自定义字段定义表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_field_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    field_name TEXT NOT NULL UNIQUE,
                    field_type TEXT DEFAULT 'text',
                    sort_order INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建自定义字段值表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_field_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password_id INTEGER NOT NULL,
                    field_id INTEGER NOT NULL,
                    value TEXT,
                    FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE,
                    FOREIGN KEY (field_id) REFERENCES custom_field_definitions(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建修改历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS modification_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建分类表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT,
                    sort_order INTEGER,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # 创建备份历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    backup_type TEXT,
                    file_path TEXT,
                    status TEXT,
                    message TEXT
                )
            ''')
            
            # 初始化默认数据
            self._init_default_data(cursor)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_default_data(self, cursor):
        """初始化默认数据"""
        try:
            # 检查是否已有分类
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            if cursor.fetchone()['count'] == 0:
                # 插入默认分类（从配置加载）
                default_categories = [
                    (cat['name'], cat['color'], 1, cat['sort_order'])
                    for cat in CategoryConfig.DEFAULT_CATEGORIES
                ]
                cursor.executemany(
                    'INSERT INTO categories (name, color, is_default, sort_order) VALUES (?, ?, ?, ?)',
                    default_categories
                )
                logger.info("已插入默认分类")
            
            # 检查是否已有设置
            cursor.execute("SELECT COUNT(*) as count FROM settings")
            if cursor.fetchone()['count'] == 0:
                # 插入默认设置（从配置加载）
                default_settings = list(SettingsConfig.DEFAULT_SETTINGS.items())
                cursor.executemany(
                    'INSERT INTO settings (key, value) VALUES (?, ?)',
                    default_settings
                )
                logger.info("已插入默认设置")
        except Exception as e:
            logger.error(f"初始化默认数据失败: {e}")
            raise
    
    # ==================== 密码管理 ====================
    
    def add_password(self, password: Password) -> int:
        """添加密码条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO passwords (
                    site_name, url, login_account, password, phone, email,
                    category, notes, register_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                password.site_name, password.url, password.login_account,
                password.password, password.phone, password.email,
                password.category, password.notes, password.register_date
            ))
            
            password_id = cursor.lastrowid
            
            # 保存自定义字段
            if password.custom_fields:
                self._save_custom_field_values(cursor, password_id, password.custom_fields)
            
            conn.commit()
            return password_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_password(self, password: Password, old_password: Optional[Password] = None):
        """更新密码条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 更新密码记录
            cursor.execute('''
                UPDATE passwords SET
                    site_name = ?, url = ?, login_account = ?, password = ?,
                    phone = ?, email = ?, category = ?, notes = ?, register_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                password.site_name, password.url, password.login_account,
                password.password, password.phone, password.email,
                password.category, password.notes, password.register_date,
                password.id
            ))
            
            # 记录修改历史
            if old_password:
                self._record_modifications(cursor, password.id, old_password, password)
            
            # 更新自定义字段
            if password.custom_fields:
                # 删除旧的自定义字段值
                cursor.execute('DELETE FROM custom_field_values WHERE password_id = ?', (password.id,))
                # 保存新的自定义字段值
                self._save_custom_field_values(cursor, password.id, password.custom_fields)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_password(self, password_id: int, soft_delete: bool = True):
        """删除密码条目（软删除或物理删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if soft_delete:
                # 软删除
                cursor.execute('''
                    UPDATE passwords SET
                        is_deleted = 1,
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (password_id,))
            else:
                # 物理删除
                cursor.execute('DELETE FROM passwords WHERE id = ?', (password_id,))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def restore_password(self, password_id: int):
        """从回收站恢复密码"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE passwords SET
                    is_deleted = 0,
                    deleted_at = NULL
                WHERE id = ?
            ''', (password_id,))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_password(self, password_id: int) -> Optional[Password]:
        """获取单个密码条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM passwords WHERE id = ?', (password_id,))
            row = cursor.fetchone()
            
            if row:
                password = self._row_to_password(row)
                # 加载自定义字段
                password.custom_fields = self._load_custom_field_values(cursor, password_id)
                return password
            return None
        finally:
            conn.close()
    
    def get_all_passwords(self, include_deleted: bool = False) -> List[Password]:
        """获取所有密码条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if include_deleted:
                cursor.execute('SELECT * FROM passwords ORDER BY created_at DESC')
            else:
                cursor.execute('SELECT * FROM passwords WHERE is_deleted = 0 ORDER BY created_at DESC')
            
            passwords = []
            for row in cursor.fetchall():
                password = self._row_to_password(row)
                # 加载自定义字段
                password.custom_fields = self._load_custom_field_values(cursor, password.id)
                passwords.append(password)
            
            return passwords
        finally:
            conn.close()
    
    def get_deleted_passwords(self) -> List[Password]:
        """获取已删除的密码条目（回收站）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM passwords WHERE is_deleted = 1 ORDER BY deleted_at DESC')
            
            passwords = []
            for row in cursor.fetchall():
                password = self._row_to_password(row)
                password.custom_fields = self._load_custom_field_values(cursor, password.id)
                passwords.append(password)
            
            return passwords
        finally:
            conn.close()
    
    def search_passwords(self, keyword: str, include_deleted: bool = False) -> List[Password]:
        """搜索密码条目"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用参数化查询避免SQL注入
            search_pattern = '%' + keyword + '%'
            
            if include_deleted:
                cursor.execute('''
                    SELECT * FROM passwords
                    WHERE (
                        site_name LIKE ? OR
                        login_account LIKE ? OR
                        email LIKE ? OR
                        phone LIKE ? OR
                        notes LIKE ? OR
                        url LIKE ?
                    )
                    ORDER BY created_at DESC
                ''', (search_pattern, search_pattern, search_pattern, 
                      search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute('''
                    SELECT * FROM passwords
                    WHERE (
                        site_name LIKE ? OR
                        login_account LIKE ? OR
                        email LIKE ? OR
                        phone LIKE ? OR
                        notes LIKE ? OR
                        url LIKE ?
                    ) AND is_deleted = 0
                    ORDER BY created_at DESC
                ''', (search_pattern, search_pattern, search_pattern,
                      search_pattern, search_pattern, search_pattern))
            
            passwords = []
            for row in cursor.fetchall():
                password = self._row_to_password(row)
                password.custom_fields = self._load_custom_field_values(cursor, password.id)
                passwords.append(password)
            
            logger.info(f"搜索关键词 '{keyword}' 找到 {len(passwords)} 条结果")
            return passwords
        except Exception as e:
            logger.error(f"搜索密码失败: {e}")
            return []
        finally:
            conn.close()
    
    def filter_by_category(self, category: str, include_deleted: bool = False) -> List[Password]:
        """按分类筛选密码"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用参数化查询避免SQL注入
            if include_deleted:
                cursor.execute('''
                    SELECT * FROM passwords
                    WHERE category = ?
                    ORDER BY created_at DESC
                ''', (category,))
            else:
                cursor.execute('''
                    SELECT * FROM passwords
                    WHERE category = ? AND is_deleted = 0
                    ORDER BY created_at DESC
                ''', (category,))
            
            passwords = []
            for row in cursor.fetchall():
                password = self._row_to_password(row)
                password.custom_fields = self._load_custom_field_values(cursor, password.id)
                passwords.append(password)
            
            logger.info(f"筛选分类 '{category}' 找到 {len(passwords)} 条结果")
            return passwords
        except Exception as e:
            logger.error(f"按分类筛选失败: {e}")
            return []
        finally:
            conn.close()
    
    def _row_to_password(self, row: sqlite3.Row) -> Password:
        """将数据库行转换为Password对象"""
        return Password(
            id=row['id'],
            site_name=row['site_name'],
            url=row['url'],
            login_account=row['login_account'],
            password=row['password'],
            phone=row['phone'],
            email=row['email'],
            category=row['category'],
            notes=row['notes'],
            register_date=row['register_date'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_deleted=bool(row['is_deleted']),
            deleted_at=row['deleted_at']
        )
    
    def _save_custom_field_values(self, cursor, password_id: int, custom_fields: Dict[str, str]):
        """保存自定义字段值"""
        for field_name, value in custom_fields.items():
            # 获取字段定义ID
            cursor.execute(
                'SELECT id FROM custom_field_definitions WHERE field_name = ?',
                (field_name,)
            )
            row = cursor.fetchone()
            if row:
                field_id = row['id']
                cursor.execute(
                    'INSERT INTO custom_field_values (password_id, field_id, value) VALUES (?, ?, ?)',
                    (password_id, field_id, value)
                )
    
    def _load_custom_field_values(self, cursor, password_id: int) -> Dict[str, str]:
        """加载自定义字段值"""
        cursor.execute('''
            SELECT cfd.field_name, cfv.value
            FROM custom_field_values cfv
            JOIN custom_field_definitions cfd ON cfv.field_id = cfd.id
            WHERE cfv.password_id = ?
            ORDER BY cfd.sort_order
        ''', (password_id,))
        
        return {row['field_name']: row['value'] for row in cursor.fetchall()}
    
    def _record_modifications(self, cursor, password_id: int, old_pwd: Password, new_pwd: Password):
        """记录字段修改历史"""
        fields_to_check = [
            ('site_name', '网站名称'),
            ('url', '网址'),
            ('login_account', '登录账号'),
            ('password', '密码'),
            ('phone', '手机号'),
            ('email', '邮箱'),
            ('category', '分类'),
            ('notes', '备注'),
            ('register_date', '注册时间')
        ]
        
        for field, display_name in fields_to_check:
            old_value = getattr(old_pwd, field, '')
            new_value = getattr(new_pwd, field, '')
            
            if old_value != new_value:
                cursor.execute('''
                    INSERT INTO modification_history (password_id, field_name, old_value, new_value)
                    VALUES (?, ?, ?, ?)
                ''', (password_id, display_name, old_value or '', new_value or ''))
    
    # ==================== 分类管理 ====================
    
    def get_all_categories(self) -> List[Category]:
        """获取所有分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM categories ORDER BY sort_order')
            categories = []
            for row in cursor.fetchall():
                categories.append(Category(
                    id=row['id'],
                    name=row['name'],
                    color=row['color'],
                    sort_order=row['sort_order'],
                    is_default=bool(row['is_default']),
                    created_at=row['created_at']
                ))
            return categories
        finally:
            conn.close()
    
    def add_category(self, category: Category) -> int:
        """添加分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO categories (name, color, sort_order, is_default)
                VALUES (?, ?, ?, ?)
            ''', (category.name, category.color, category.sort_order, category.is_default))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_category(self, category: Category):
        """更新分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE categories SET
                    name = ?, color = ?, sort_order = ?
                WHERE id = ?
            ''', (category.name, category.color, category.sort_order, category.id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_category(self, category_id: int) -> bool:
        """删除分类（需要检查是否有密码使用）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否有密码使用此分类
            cursor.execute(
                'SELECT name FROM categories WHERE id = ?',
                (category_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            
            category_name = row['name']
            cursor.execute(
                'SELECT COUNT(*) as count FROM passwords WHERE category = ? AND is_deleted = 0',
                (category_name,)
            )
            count = cursor.fetchone()['count']
            
            if count > 0:
                return False  # 有密码使用，不能删除
            
            # 删除分类
            cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_category_usage_count(self, category_name: str) -> int:
        """获取分类的使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT COUNT(*) as count FROM passwords WHERE category = ? AND is_deleted = 0',
                (category_name,)
            )
            return cursor.fetchone()['count']
        finally:
            conn.close()
    
    # ==================== 自定义字段管理 ====================
    
    def get_all_custom_fields(self) -> List[CustomField]:
        """获取所有自定义字段定义"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM custom_field_definitions ORDER BY sort_order')
            fields = []
            for row in cursor.fetchall():
                fields.append(CustomField(
                    id=row['id'],
                    field_name=row['field_name'],
                    field_type=row['field_type'],
                    sort_order=row['sort_order'],
                    created_at=row['created_at']
                ))
            return fields
        finally:
            conn.close()
    
    def add_custom_field(self, field: CustomField) -> int:
        """添加自定义字段定义"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO custom_field_definitions (field_name, field_type, sort_order)
                VALUES (?, ?, ?)
            ''', (field.field_name, field.field_type, field.sort_order))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_custom_field(self, field_id: int) -> bool:
        """删除自定义字段（需要检查使用情况）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查是否有值使用此字段
            cursor.execute(
                'SELECT COUNT(*) as count FROM custom_field_values WHERE field_id = ?',
                (field_id,)
            )
            count = cursor.fetchone()['count']
            
            if count > 0:
                return False  # 有值使用，不能删除
            
            # 删除字段定义
            cursor.execute('DELETE FROM custom_field_definitions WHERE id = ?', (field_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_custom_field_usage_count(self, field_id: int) -> int:
        """获取自定义字段的使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT COUNT(*) as count FROM custom_field_values WHERE field_id = ?',
                (field_id,)
            )
            return cursor.fetchone()['count']
        finally:
            conn.close()
    
    # ==================== 修改历史 ====================
    
    def get_modification_history(self, password_id: int) -> List[ModificationHistory]:
        """获取密码条目的修改历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM modification_history
                WHERE password_id = ?
                ORDER BY modified_at DESC
            ''', (password_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append(ModificationHistory(
                    id=row['id'],
                    password_id=row['password_id'],
                    field_name=row['field_name'],
                    old_value=row['old_value'],
                    new_value=row['new_value'],
                    modified_at=row['modified_at']
                ))
            return history
        finally:
            conn.close()
    
    # ==================== 设置管理 ====================
    
    def get_setting(self, key: str, default: str = "") -> str:
        """获取设置值"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
        finally:
            conn.close()
    
    def set_setting(self, key: str, value: str):
        """设置值"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_all_settings(self) -> Dict[str, str]:
        """获取所有设置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT key, value FROM settings')
            return {row['key']: row['value'] for row in cursor.fetchall()}
        finally:
            conn.close()
    
    # ==================== 备份历史 ====================
    
    def add_backup_history(self, backup: BackupHistory) -> int:
        """添加备份历史记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO backup_history (backup_type, file_path, status, message)
                VALUES (?, ?, ?, ?)
            ''', (backup.backup_type, backup.file_path, backup.status, backup.message))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_backup_history(self, limit: int = 20) -> List[BackupHistory]:
        """获取备份历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM backup_history
                ORDER BY backup_time DESC
                LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append(BackupHistory(
                    id=row['id'],
                    backup_time=row['backup_time'],
                    backup_type=row['backup_type'],
                    file_path=row['file_path'],
                    status=row['status'],
                    message=row['message']
                ))
            return history
        finally:
            conn.close()

