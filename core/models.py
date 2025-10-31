"""
数据模型 - 定义数据结构
"""
from datetime import datetime
from typing import Optional, List, Dict, Any


class Password:
    """密码条目模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 site_name: str = "",
                 url: str = "",
                 login_account: str = "",
                 password: str = "",
                 phone: str = "",
                 email: str = "",
                 category: str = "",
                 notes: str = "",
                 register_date: Optional[str] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None,
                 is_deleted: bool = False,
                 deleted_at: Optional[str] = None):
        self.id = id
        self.site_name = site_name
        self.url = url
        self.login_account = login_account
        self.password = password
        self.phone = phone
        self.email = email
        self.category = category
        self.notes = notes
        self.register_date = register_date or datetime.now().strftime('%Y-%m-%d')
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_deleted = is_deleted
        self.deleted_at = deleted_at
        
        # 自定义字段
        self.custom_fields: Dict[str, str] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'site_name': self.site_name,
            'url': self.url,
            'login_account': self.login_account,
            'password': self.password,
            'phone': self.phone,
            'email': self.email,
            'category': self.category,
            'notes': self.notes,
            'register_date': self.register_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at,
            'custom_fields': self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Password':
        """从字典创建对象"""
        pwd = cls(
            id=data.get('id'),
            site_name=data.get('site_name', ''),
            url=data.get('url', ''),
            login_account=data.get('login_account', ''),
            password=data.get('password', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            category=data.get('category', ''),
            notes=data.get('notes', ''),
            register_date=data.get('register_date'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_deleted=data.get('is_deleted', False),
            deleted_at=data.get('deleted_at')
        )
        pwd.custom_fields = data.get('custom_fields', {})
        return pwd


class Category:
    """分类模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 name: str = "",
                 color: str = "#999999",
                 sort_order: int = 0,
                 is_default: bool = False,
                 created_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.color = color
        self.sort_order = sort_order
        self.is_default = is_default
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'sort_order': self.sort_order,
            'is_default': self.is_default,
            'created_at': self.created_at
        }


class CustomField:
    """自定义字段定义模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 field_name: str = "",
                 field_type: str = "text",
                 sort_order: int = 0,
                 created_at: Optional[str] = None):
        self.id = id
        self.field_name = field_name
        self.field_type = field_type
        self.sort_order = sort_order
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'sort_order': self.sort_order,
            'created_at': self.created_at
        }


class ModificationHistory:
    """修改历史模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 password_id: int = 0,
                 field_name: str = "",
                 old_value: str = "",
                 new_value: str = "",
                 modified_at: Optional[str] = None):
        self.id = id
        self.password_id = password_id
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
        self.modified_at = modified_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'password_id': self.password_id,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'modified_at': self.modified_at
        }


class BackupHistory:
    """备份历史模型"""
    
    def __init__(self,
                 id: Optional[int] = None,
                 backup_time: Optional[str] = None,
                 backup_type: str = "",
                 file_path: str = "",
                 status: str = "",
                 message: str = ""):
        self.id = id
        self.backup_time = backup_time
        self.backup_type = backup_type
        self.file_path = file_path
        self.status = status
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'backup_time': self.backup_time,
            'backup_type': self.backup_type,
            'file_path': self.file_path,
            'status': self.status,
            'message': self.message
        }

